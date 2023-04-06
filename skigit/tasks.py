"""
Celery tasks in the skigit app!
"""
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import os, ffmpy, hashlib, random, subprocess
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User
from constance import config

from skigit.models import UploadedVideo, Video, Thumbnail, VideoDetail, Category, SubjectCategory, Donation, Incentive
from skigit.storage import B2Storage
from user.models import BusinessLogo
from core.utils import get_object_or_None
from friends.models import Notification
from mailpost.models import EmailTemplate
from skigit.admin import approve_video
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from skigit.thumbnails import SkigitThumbnail

logger = logging.getLogger('Skigit')


@shared_task(bind=True)
def video_compression_and_upload(self, data):
#def video_compression_and_upload(data):
    """

    Compress uploaded video and upload to black blaze - we don't wait user to wait
    Notify user by email if any issue occur in the operation
    """
    cur_user = get_object_or_None(User, id=data['user_id'])

    try:
        uploaded_video = get_object_or_None(UploadedVideo, id=data['uploaded_video_id'])


        b2 = B2Storage()
        # Youtube Video API Upload call

        h = hashlib.blake2b(digest_size=20)
        h.update(data['title'].encode('utf-8'))

        filename = h.hexdigest()

        # get the video duration to calculate where we will get the picture
        video_path = uploaded_video.file_on_server.path
        ff = ffmpy.FFprobe(
            inputs={video_path: None},
            global_options='-show_entries format=duration -v quiet -of csv="p=0"'
        )

        stdout, stderr = ff.run(stdout=subprocess.PIPE)
        ff.process.terminate()

        split_seconds = random.randint(0, int(float(stdout.rsplit()[0])))

        # Convert seconds to a time string "[[[DD:]HH:]MM:]SS".

        dhms = ''
        for scale in 86400, 3600, 60:
            result, seconds = divmod(split_seconds, scale)
            if dhms != '' or result > 0:
                dhms += '{0:02d}:'.format(result)
        dhms += '{0:02d}'.format(seconds)

        # verify if the image exists. If exists remove it and upload again
        for file_info, folder_name in b2.bucket().ls(show_versions=False):
            if file_info.file_name == '{}.jpg'.format(filename):
                b2.bucket().delete_file_version(file_info.id_, '{}.jpg'.format(filename))

        # Creating Thumbnail Entry for Uploaded Videos
        ff = ffmpy.FFmpeg(
            inputs={video_path: None},
            outputs={'pipe:1': '-ss {} -qscale:v 2 -f image2pipe -vframes 1 -v quiet'.format(dhms)}
        )

        stdout, stderr = ff.run(stdout=subprocess.PIPE)
        ff.process.terminate()

        thumbnailObj = None
        if stdout:
            img_temp = NamedTemporaryFile() ## this is default: delete=True)
            img_temp.write(stdout)
            img_temp.flush()

            # Store original raw image
            b2.upload(
                img_temp.name,
                SkigitThumbnail().THUMBNAIL_ORIGINAL_FOLDER+'{}.jpg'.format(filename)
            )

            # Generate the corresponding thumbnail and store it localy
            tmb = SkigitThumbnail(img_temp.name)
            tmb.save_thumbnail('media/{}.jpg'.format(filename))
                      
            # Store thumbnail image
            uploaded_image = b2.upload(
                tmb.output_path,
                '{}.jpg'.format(filename)
            )

            # create thumbnail object without video as it's not ready yet
            thumbnailObj = Thumbnail.objects.create(file_id=uploaded_image.id_, filename='{}.jpg'.format(filename))

            # Close and remove temporary local files
            img_temp.close()
            tmb.remove_local_thumbnail()


        # lets start the compression process

        file_name_with_ext = uploaded_video.file_on_server.name

        compressOptions = ['-vcodec', 'libx264', '-crf', data['crf'], '-strict', '-2', '-y']

        # check audio exist in input file
        ffaudio = ffmpy.FFprobe(
                inputs={uploaded_video.file_on_server.path: None},
                global_options='-show_streams -select_streams a -loglevel error'
            )
        isAudio = (ffaudio.run(stdout=subprocess.PIPE))[0].decode('utf-8')
        ffaudio.process.terminate()

        if not isAudio:
            compressOptions.append('-an')

        # convert compressed video into mp4 format
        compressed_filename_with_ext = '{}.mp4'.format(os.path.splitext(os.path.basename(file_name_with_ext))[0])

        ff = ffmpy.FFmpeg(
            inputs={uploaded_video.file_on_server.path: None},
            outputs={'media/videos/{}'.format(compressed_filename_with_ext): compressOptions},
        )
        ff.run()
        ff.process.terminate() # added to clean the process and allow deletion

        # remove original video from temp folder
        os.remove("media/videos/temp/{}".format(os.path.basename(file_name_with_ext)))
        # update uploaded video reference to compressed video
        uploaded_video.file_on_server.name = 'videos/{}'.format(compressed_filename_with_ext)
        uploaded_video.save()

        # delete video if exist for that skigit
        Video.objects.filter(filename='{}.mp4'.format(filename)).delete()

        # verify if the image exists. If exists remove it and upload again
        for file_info, folder_name in b2.bucket().ls(show_versions=False):
            if file_info.file_name == '{}.mp4'.format(filename):
                b2.bucket().delete_file_version(file_info.id_, '{}.mp4'.format(filename))

        b2_video = b2.upload(
            uploaded_video.file_on_server.path,
            '{}.mp4'.format(filename)
        )

        if b2_video:
            video_id = b2_video.id_

            # save video_id to video instance
            video = Video(user=cur_user,
                          video_id=video_id,
                          filename='{}.mp4'.format(filename),
                          title=data['title'],
                          description=data['why_rocks'],
                          created_by=cur_user)
            video.save()

            if thumbnailObj is not None:
                # attach thumbnail to video
                thumbnailObj.video = video
                thumbnailObj.save()

            # remove temporary video file
            # os.unlink(uploaded_video.file_on_server.path)
            os.remove(uploaded_video.file_on_server.path)

            skigit_form = VideoDetail()
            skigit_form.title = data['title']
            if data['category']:
                category = Category.objects.get(id=data['category'])
                skigit_form.category = category
            if data['subject_category']:
                subject_category = SubjectCategory.objects.get(id=data['subject_category'])
                skigit_form.subject_category = subject_category
            skigit_form.add_logo = data['add_logo']
            skigit_form.receive_donate_sperk = data['receive_donate_sperk']
            skigit_form.why_rocks = data['why_rocks']
            if data['made_by']:
                user = User.objects.get(id=int(data["made_by"]))
                skigit_form.made_by = user
                skigit_form.business_user = user
            if data["made_by_option"]:
                skigit_form.made_by_option = data["made_by_option"]

            skigit_form.skigit_id = video
            skigit_form.share_skigit = video
            if data['add_logo'] == '1' and (
                    not data['select_logo'] == 'undefined' and not data['select_logo'] == '') and \
                    BusinessLogo.objects.filter(id=data['select_logo']).exists():
                busness_logo = BusinessLogo.objects.get(id=data['select_logo'])
                skigit_form.business_logo = busness_logo
                skigit_form.is_sperk = True
                if data['receive_donate_sperk'] != 'undefined' and data['receive_donate_sperk'] != '':
                    if int(data['receive_donate_sperk']) == 2:
                        if data['donate_skigit'] != 'undefined' and data['donate_skigit'] != '':
                            donate = get_object_or_None(Donation, id=data['donate_skigit'])
                            if donate:
                                skigit_form.donate_skigit = donate

                    # check if bussiness user has offered incentive,
                    # also if user selected one of Receieve or Donate option
                    if data['made_by'] and user.profile.incentive == 1 and int(data['receive_donate_sperk']) in [1, 2]:

                        incentive = Incentive()
                        incentive.amount = user.profile.incetive_val
                        incentive.user = user
                        incentive.sperk_type = int(data['receive_donate_sperk'])
                        incentive.title = 'Incentive for %s skigit' % skigit_form.title
                        incentive.is_active = False
                        incentive.billing_month = datetime.now().date()
                        incentive.save()

                        skigit_form.incentive = incentive

            skigit_form.bought_at = data['bought_at']
            skigit_form.why_rocks = data['why_rocks']
            receive_donate_sperk = data['receive_donate_sperk']
            if receive_donate_sperk == '' or receive_donate_sperk == 'undefined':
                skigit_form.receive_donate_sperk = 0

            if data['plugin_upload']:
                video_detail = get_object_or_None(VideoDetail, id=data['plug_id'])
                plugged_video = get_object_or_None(Video, id=video_detail.skigit_id.id)
                skigit_form.is_plugged = True
                skigit_form.plugged_skigit = plugged_video
                skigit_form.share_skigit = video

            skigit_form.created_by = cur_user
            skigit_form.view_count = 0
            skigit_form.save()

            # delete the uploaded video instance
            uploaded_video.delete()

            Notification.objects.create(msg_type='video_uploaded', skigit_id=skigit_form.skigit_id.id,
                                                            user=skigit_form.skigit_id.user, from_user=cur_user,  message="Your video has been successfully uploaded. You'll be notified when it's ready")
            
            if config.VIDEOS_AUTO_APPROVAL:
                approve_video(skigit_form)
        else:
            logger.error("=======B2 video not uploaded========== ")
            Notification.objects.create(msg_type='video_not_uploaded', user=cur_user, from_user=cur_user,  message="Your video is not successfully uploaded. please try again.")
            EmailTemplate.send(
                template_key="your_skigit_video_not_uploaded",
                emails=cur_user.email,
                context={"title": data['title']}
            )
    except Exception as exc:
        logger.error("============Video not uploaded============== :", exc)
        Notification.objects.create(msg_type='video_not_uploaded', user=cur_user, from_user=cur_user,  message="Your video is not successfully uploaded. please try again.")
        EmailTemplate.send(
            template_key="your_skigit_video_not_uploaded",
            emails=cur_user.email,
            context={"title": data['title']}
        )

@shared_task
def permanently_delete_video():
    if config.AUTO_DELETE_VIDEO:
        # delete videos permanently that are temporarily deleted or rejected for 30 days
        date_before_thirty_days = timezone.now() - timedelta(days=config.DAYS_COUNT_FOR_AUTO_DELETE_BOT)
        vdo_detail_objs = VideoDetail.objects.filter(status__in=[2,3], deleted_at__lte=date_before_thirty_days)
        for vdo_detail_obj in vdo_detail_objs:
            child_plug = VideoDetail.objects.filter(plugged_skigit=vdo_detail_obj.skigit_id, is_plugged=True,
                                                    status=1)
            if child_plug.exists():
                if VideoDetail.objects.filter(skigit_id=vdo_detail_obj.plugged_skigit, is_plugged=True, status=1).exists():
                    parent_plug = VideoDetail.objects.get(skigit_id=vdo_detail_obj.plugged_skigit, is_plugged=True,
                                                          status=1)
                    VideoDetail.objects.filter(id__in=child_plug, status=1).update(
                        plugged_skigit=parent_plug.skigit_id.id)

                elif vdo_detail_obj.is_plugged == False:
                    VideoDetail.objects.filter(plugged_skigit=vdo_detail_obj.skigit_id, status=1).update(is_plugged=False)

        Video.objects.filter(id__in=vdo_detail_objs.values_list('skigit_id_id', flat=True)).delete()
