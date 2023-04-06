import os, math, json
import operator
from urllib import response
import uuid
import requests
import hashlib
import random
from datetime import datetime
from datetime import timedelta
import urllib
from heapq import merge
import logging
from PIL import Image, ExifTags
from user.forms import ProfileNotificationForm
from user.models import BusinessLogo, Profile
from constance import config
from allauth.account.signals import email_confirmed, user_signed_up
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q, F, Count
from django.dispatch import receiver
from django.http import HttpResponseRedirect, JsonResponse
from django.template.defaultfilters import safe

from django.shortcuts import get_object_or_404, render
from django.template.context_processors import csrf
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.generic import TemplateView, View
from django.urls import reverse
from django.contrib.auth.models import Group

from social.models import Follow, Plugged, Share
from sorl.thumbnail import get_thumbnail
from rest_framework import views, generics, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from core.utils import (create_share_thumbnails, get_related_users, get_user_type, is_user_business, payment_required,
                        require_filled_profile, get_all_logged_in_users, get_video_share_url, get_object_or_None,
                        CustomIsAuthenticated, deleteDisabled, delete_user_account, user_invoices_cleared,states_list_By_country,
                         is_verified_business_user,cal_age_bins)
from core.views import SkigitBaseView
from core.serializers import CategorySerializer, SubjectCategorySerializer
from friends.models import Embed, Friend, Notification
from friends.views import notification_settings, get_time_delta, get_friends_list, get_general_notifications_count
from invoices.models import EmbedInvoice, BusinessLogoInvoice
from invoices.views import business_share_invoice,qr_code_fees
from mailpost.models import EmailTemplate
from skigit.forms import (CopyrightInfringementForm, SkigitUploadForm, YoutubeDirectUploadForm,
                          YoutubeLinkUploadForm, DeleteProfileForm)
from skigit.models import (Category, Donation, Favorite, InappropriateSkigitReason, Incentive, Like, SubjectCategory,
                           Thumbnail, UploadedVideoLink, Video, VideoDetail, InappropriateSkigit, BugReport,
                           UploadedVideo)
from skigit.serializers import (VideoDetailSerializer, BugReportSerializer, PluginVideoSerializer,
                                InappropriateReasonSerializer, CopyrightInfringementSerializer,
                                VideoUploadSerializer)
from user.serializers import (ProfileFriendSerializer, BusinessLogoSerializer,
                              ProfileBusinessSerializer, ExtraProfileImageSerializer,
                              BusinessProfileDetailSerializer, api_request_images)
from user.models import ProfileUrl
from skigit.tasks import video_compression_and_upload
from skigit.admin import approve_video, unapprove_video
from invoices.views import updateMonthlyLogoInvoice
from sperks.serializers import DonationSerializer
from django.core.cache import cache
import string
from django.core.files.storage import FileSystemStorage
import itertools
from invoices.models import *

logger = logging.getLogger('Skigit')


# @method_decorator(payment_required, name='dispatch')
# @method_decorator(require_filled_profile, name='dispatch')
# class CategoryDetail(TemplateView):
#     def get(self, request, cat_slug=None, *args, **kwargs):
#
#         page_template = 'category/category_body.html'
#
#         video_detail = []
#         like_dict = []
#         share_dict = []
#         plug_dict = []
#
#         category_current = Category.objects.get(cat_slug=cat_slug)
#         vid_latest_uploaded = VideoDetail.objects.select_related('skigit_id')
#         vid_latest_uploaded = vid_latest_uploaded.filter(status=1, is_active=True)
#         vid_latest_uploaded = vid_latest_uploaded.filter(category=category_current)
#
#         if request.method == 'POST' and request.POST.get('sort', '') == '0':
#
#             vid_latest_uploaded = vid_latest_uploaded.order_by('updated_date')
#
#             if vid_latest_uploaded:
#                 vid_latest_uploaded = vid_latest_uploaded[0]
#             videos = VideoDetail.objects.filter(category=category_current, status=1,
#                                                 is_active=True).order_by('updated_date')
#             for vid in videos:
#                 like_count = Like.objects.filter(skigit=vid.skigit_id, status=True).count()
#                 like_dict.append({'id': vid.id, 'count': like_count})
#                 video_share = Share.objects.filter(skigit_id=vid, is_active=True).count()
#                 share_dict.append({'id': vid.id, 'count': video_share})
#                 video_plug = VideoDetail.objects.filter(plugged_skigit=vid.skigit_id, is_plugged=True, status=1).count()
#                 plug_dict.append({'id': vid.id, 'count': video_plug})
#                 video_detail.append(vid)
#                 if vid.made_by:
#                     us_profile = Profile.objects.get(user=vid.made_by)
#                     if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
#                         vid.default_business_logo = us_profile.logo_img.filter(is_deleted=False).all()[0]
#                     else:
#                         vid.default_business_logo = ''
#                 else:
#                     vid.default_business_logo = ''
#                 video_detail.append(vid)
#
#             ski_share_list = []
#             for vid_data in videos:
#                 sharObj = Share.objects.filter(skigit_id=vid_data, is_active=True,
#                                                user=request.user.id).order_by('to_user', '-pk').distinct('to_user')
#                 for sh in sharObj:
#                     ski_share_list.append({'share_date': sh.created_date, 'username': sh.to_user.username,
#                                            'vid': sh.skigit_id_id})
#
#             like_skigit = []
#             video_likes = Like.objects.filter(user_id=request.user.id, status=True)
#             for likes in video_likes:
#                 like_skigit.append(likes.skigit_id)
#             context = {
#                 'page_template': page_template,
#                 'category_current': category_current,
#                 'video_detail': video_detail,
#                 'vid_latest_uploaded': vid_latest_uploaded,
#                 'video_share': share_dict,
#                 'video_plug': plug_dict,
#                 'video_likes': like_skigit,
#                 'like_count': like_dict,
#                 'skigit_list': ski_share_list,
#                 'order': 1,
#                 'order_title': 1,
#                 'order_views': 1,
#                 'order_random': 1,
#                 'order_likes': 1,
#                 'page_type': 'categorys',
#                 'users': get_all_logged_in_users()
#             }
#             if request.is_ajax():
#                 template = page_template
#             return render(request, template, context)
#         else:
#             vid_latest_uploaded = vid_latest_uploaded.order_by('-updated_date')
#             ski_share_list = []
#             if vid_latest_uploaded:
#                 vid_latest_uploaded = vid_latest_uploaded[0]
#             videos = VideoDetail.objects.filter(category=category_current, status=1, is_active=True).order_by(
#                 '-updated_date')
#             for vid in videos:
#                 like_count = Like.objects.filter(skigit=vid.skigit_id, status=True).count()
#                 like_dict.append({'id': vid.id, 'count': like_count})
#                 video_share = Share.objects.filter(skigit_id=vid, is_active=True).count()
#                 share_dict.append({'id': vid.id, 'count': video_share})
#                 video_plug = VideoDetail.objects.filter(plugged_skigit=vid.skigit_id, is_plugged=True, status=1).count()
#                 plug_dict.append({'id': vid.id, 'count': video_plug})
#                 sharObj = Share.objects.filter(skigit_id=vid, is_active=True, user=request.user.id).order_by('to_user',
#                                                                                                              '-pk').distinct(
#                     'to_user')
#                 for sh in sharObj:
#                     ski_share_list.append(
#                         {'share_date': sh.created_date, 'username': sh.to_user.username, 'vid': sh.skigit_id_id})
#                 if vid.made_by:
#                     us_profile = Profile.objects.get(user=vid.made_by)
#                     if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
#                         vid.default_business_logo = us_profile.logo_img.filter(is_deleted=False).all()[0]
#                     else:
#                         vid.default_business_logo = ''
#                 else:
#                     vid.default_business_logo = ''
#                 video_detail.append(vid)
#             like_skigit = []
#             video_likes = Like.objects.filter(user_id=request.user.id, status=True)
#             for likes in video_likes:
#                 like_skigit.append(likes.skigit_id)
#
#         friend_list = []
#         if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1).exists():
#             f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1)
#             from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user', flat=True).distinct()
#             to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user', flat=True).distinct()
#             fr_list = list(merge(from_user_list, to_user_list))
#             friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')
#             for friends in friends_detail:
#                 if friends.profile_img:
#                     l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
#                 else:
#                     l_img = "{0}{1}".format(settings.STATIC_URL,'images/noimage_user.jpg')
#                 friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
#                                     'name': friends.user.get_full_name(), 'image': l_img})
#
#         context = {
#             'category_current': category_current,
#             'video_detail': video_detail,
#             'page_template': page_template,
#             'vid_latest_uploaded': vid_latest_uploaded,
#             'friend_list': friend_list,
#             'video_share': share_dict,
#             'video_plug': plug_dict,
#             'video_likes': like_skigit,
#             'like_count': like_dict,
#             'skigit_list': ski_share_list,
#             'order': 1,
#             'order_views': 1,
#             'order_title': 1,
#             'order_random': 1,
#             'order_likes': 1,
#             'page_type': 'categorys',
#             'users': get_all_logged_in_users()
#         }
#         if request.is_ajax():
#             template = page_template
#         return render(request, 'category/category_bash.html', context)


# Generic functions

def get_followers(user_id):
    follow_list = []
    user = get_object_or_None(User, pk=user_id)
    follow_record = Follow.objects.filter(user=user.id, status=True).order_by('-follow__first_name')

    for following in follow_record:
        if User.objects.exclude(id=user.id).filter(id=following.follow.id).exists():
            user_follow_detail = User.objects.exclude(id=user.id).filter(id=following.follow.id)
            for user_detail in user_follow_detail:
                user_profile = Profile.objects.get(user=user_detail)
                follow_list.append(user_profile)
    follow_list = sorted(follow_list, key=lambda follow: user_detail.get_full_name())
    return follow_list


def get_user_plugged_videos(user_id):
    '''

    :param user_id:
    :return: the list of user plugged videos
    '''
    plug_skigit_list = []
    # logger.info("Plugged USER ID = ", user_id)
    user = get_object_or_None(User, pk=user_id)
    skigit_plug = user.username
    vid_record = Video.objects.filter(user=user.id).values_list('id', flat=True).order_by('-created_date')
    if VideoDetail.objects.filter(skigit_id__id__in=vid_record, status=True, is_plugged=True).exists():
        plug_id = VideoDetail.objects.filter(skigit_id__id__in=vid_record, status=True,
                                             is_plugged=True).values_list('skigit_id', flat=True)
        vid = VideoDetail.objects.filter(skigit_id__id__in=plug_id, status=True,
                                         plugged_skigit__id__gte=1)
        for vid_profile in vid:
            try:

                pluged_videos = VideoDetail.objects.get(title=vid_profile.plugged_skigit.title, status=True)
                if pluged_videos not in plug_skigit_list and pluged_videos is not None:
                    plug_skigit_list.append(pluged_videos)
            except ObjectDoesNotExist:
                continue
    return plug_skigit_list


def get_error_result(errors):
    result = {'status': '',
              'message': ''}

    for k, v in errors.items():
        result.update(status='error',
                      message="{0} - {1}".format(k, v[0]))
        break
    return result


def get_company_urls(profile_url):
    '''

    :param profile_url:
    :return: Profile URLs of business users
    '''

    profile_urls = []

    if profile_url.url1:
        profile_urls.append({'name': profile_url.disc1 if profile_url.disc1 else '',
                             'url': profile_url.url1})
    if profile_url.url2:
        profile_urls.append({'name': profile_url.disc2 if profile_url.disc2 else '',
                             'url': profile_url.url2})
    if profile_url.url3:
        profile_urls.append({'name': profile_url.disc3 if profile_url.disc3 else '',
                             'url': profile_url.url3})
    if profile_url.url4:
        profile_urls.append({'name': profile_url.disc4 if profile_url.disc4 else '',
                             'url': profile_url.url4})
    if profile_url.url5:
        profile_urls.append({'name': profile_url.disc5 if profile_url.disc5 else '',
                             'url': profile_url.url5})
    return profile_urls


def get_video_share_image_url(video_id):
    video_detail = get_object_or_None(VideoDetail, id=video_id)
    u_profile = get_object_or_None(Profile, user=video_detail.skigit_id.user)
    # company_logo_url = get_thumbnail(u_profile.profile_img, '100x100', quality=99).url
    company_logo_url = api_request_images(u_profile.profile_img, quality=99, format='PNG')
    # logger.info("Company LOGO URL ==>", company_logo_url)
    image_url = ''

    if video_detail.business_logo and video_detail.made_by:
        if video_detail.business_logo.is_deleted is False:
            # skigit_b_logo = get_thumbnail(video_detail.business_logo.logo, '100x100', quality=99).url
            skigit_b_logo = api_request_images(video_detail.business_logo.logo, quality=99, format='PNG')
            image_url = create_share_thumbnails(video_detail, video_detail.skigit_id.thumbnails.all()[0].url(),
                                                # "{0}{1}".format(settings.HOST, skigit_b_logo),
                                                # "{0}{1}".format(settings.HOST, company_logo_url))
                                                "{0}".format(skigit_b_logo),
                                                "{0}".format(company_logo_url))
            logger.info("Image URL 1 ==>", image_url)
        elif video_detail.business_logo.is_deleted is True:
            u_profile = Profile.objects.get(user=video_detail.made_by)
            if u_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                blogo = u_profile.logo_img.filter(is_deleted=False).all()[0]
                # skigit_b_logo = get_thumbnail(blogo.logo, '100x100', quality=99).url
                skigit_b_logo = api_request_images(blogo.logo, quality=99, format='PNG')
                image_url = create_share_thumbnails(video_detail, video_detail.skigit_id.thumbnails.all()[0].url(),
                                                    # "{0}{1}".format(settings.HOST, skigit_b_logo),
                                                    # "{0}{1}".format(settings.HOST, company_logo_url))
                                                    "{0}".format(skigit_b_logo),
                                                    "{0}".format(company_logo_url))
                logger.info("Image URL 2 ==>", image_url)
    else:
        image_url = create_share_thumbnails(video_detail, video_detail.skigit_id.thumbnails.all()[0].url())
        logger.info("Image URL ==>", image_url)
    image_url = "{0}{1}".format(settins.MEDIA_HOST_URL, image_url) if image_url else "{0}{1}".format(settings.STATIC_HOST_URL, 'images/logo.png')
    return image_url


def unplug_video(user_id, video_id):
    response_data = {'is_success': False, 'message': 'Error in un-plug video'}

    try:
        user = get_object_or_None(User, id=user_id)
        # check if the video which is plugged exists
        if VideoDetail.objects.filter(id=video_id, status=True).exists():
            vid_record = VideoDetail.objects.get(id=video_id, status=True)
            # check the video used to plug other video exists
            if VideoDetail.objects.filter(plugged_skigit=vid_record.skigit_id, skigit_id__user=user).exists():
                # remove the plug
                VideoDetail.objects.filter(plugged_skigit=vid_record.skigit_id, skigit_id__user=user) \
                    .update(plugged_skigit=None)
                # remove entry from Plugged table
                plugged_record = Plugged.objects.filter(skigit=vid_record.skigit_id_id, user=user,
                                                        plugged=vid_record.skigit_id.user.id)
                plugged_record.delete()
                # check if there is no more plug exist for that video
                if not VideoDetail.objects.filter(plugged_skigit=vid_record.skigit_id).exists():
                    # then set plug to false
                    vid_record.is_plugged = False
                    vid_record.save()

                if notification_settings(vid_record.skigit_id.user.id, 'un_plug_notify'):
                    f_nt_message = " "
                    f_nt_message += " We're sorry... your got unplugged."
                    f_nt_message += user.username
                    f_nt_message += " unplugged from your Skigit"
                    f_nt_message += vid_record.title + '.'
                    Notification.objects.create(msg_type='un_plug', skigit_id=vid_record.skigit_id.id,
                                                user=vid_record.skigit_id.user,
                                                from_user=user, message=f_nt_message)
            response_data['is_success'] = True
            response_data['message'] = " %s Skigit was Unplugged. \r\n" % vid_record.title
        else:
            response_data = {'is_success': True, 'message': 'The video is unplugged already.'}
    except Exception as exc:
        logger.error("Un plug video: ", exc)
        response_data['is_success'] = False
        response_data['message'] = "Error in un-plug video"
    return response_data


def mark_video_as_deleted(user_id, video_id):
    response_data = {'is_success': False, 'message': 'Error in delete ajax call'}
    try:
        vdo_detail_obj = VideoDetail.objects.get(id=video_id, skigit_id__user__id=user_id)
        if deleteDisabled(vdo_detail_obj):
            response_data['is_success'] = False
            response_data['message'] = "This Skigit cannot be deleted because you received a Skitbit for creating it" \
                                       " so it must remain posted for 30 days. You can delete it on {}. " \
                                       "Refer to Skigit Terms and Conditions" \
                                       "".format(vdo_detail_obj.published_at + timedelta(days=30))
            return response_data

        Notification.objects.filter(skigit_id=vdo_detail_obj.skigit_id.id).delete()
        vdo_detail_obj.status = 3
        vdo_detail_obj.deleted_at = datetime.now()
        vdo_detail_obj.save()
        response_data['is_success'] = True
        response_data['message'] = " %s Skigit was deleted. \r\n" % vdo_detail_obj.title
    except Exception as exc:
        logger.error("Safe Video Delete: ", exc)
        response_data['is_success'] = False
        response_data['message'] = "Error occured while deleting skigit."
    return response_data


def get_business_logos(user):
    return [i for i in user.profile.logo_img.filter(is_deleted=False).values("logo")]


def get_profile_extra_images(user):
    return [i for i in user.profile.extra_profile_img.values("profile_img")]


def upload_image(files, file_field_name, filepath):
    context = {'is_success': False,
               'message': ''}
    try:
        if not files[file_field_name].name.lower().endswith(('.jpg', '.jpeg', '.gif', '.png')):
            context.update(
                {'is_success': False,
                 'message': "Please select valid file format like *.jpg, *.jpeg, *.gif, *.png ",
                 'valid_format': False})
            return context
        image = Image.open(filepath)
        # unfortunately Pillow==4.1.1 does't provide _getexif support for PNG images
        if hasattr(image, '_getexif') and image._getexif():
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break

            exif = dict(image._getexif().items())
            try:
                if exif[orientation] == 3:
                    image = image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image = image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image = image.rotate(90, expand=True)
            except KeyError:
                pass
        image.save(filepath)
        image.close()
        context.update(is_success=True)
    except Exception as exc:
        logger.error("Image is not uploaded:", exc)
        context.update(is_success=False,
                       message="The image is not uploaded successfully!")
    return context

def validate_doc_type(files, file_field_name):
    context = {'is_success': False, 'message': ''}

    try:
        if not files[file_field_name].name.lower().endswith(('.doc', '.docx', '.pdf')):
            context.update({'is_success': False, 'message':"Please select valid file format like *.doc, *.docx, *.pdf", 'valid_format': False})
            return context

    except Exception as exc:
        logger.error("Documentation is not uploaded:", exc)
        context.update(is_success=False, message="The documentation is not uploaded successfully!")

    return context


def upload_profile_image(user, files, file_field_name='file', api_request=False):
    context = {'is_success': False,
               'message': ''}

    try:
        filepath = handle_uploaded_file(files[file_field_name], files[file_field_name].name)
        response_data = upload_image(files, file_field_name, filepath)
        context = response_data
        if response_data['is_success']:
            profile = Profile.objects.get(user=user)
            profile.profile_img = "skigit/profile/%s" % files[file_field_name].name
            profile.save()
            if api_request:
                context.update({'is_success': True,
                                'message': 'The profile image is uploaded successfully.',
                                'data': {
                                    'new_image': '{0}{1}'.format(settings.MEDIA_URL, profile.profile_img)
                                }})
            else:
                context.update({"is_success": True,
                                "message": "{0}skigit/profile/{1}".format(settings.MEDIA_URL,
                                                                          files[file_field_name].name),
                                "valid_format": True})
    except Exception as exc:
        logger.error("Profile image is not uploaded:", exc)
        context.update({'is_success': False,
                        'message': 'The profile image is not uploaded successfully. Please try again.'})
    return context


def upload_extra_profile_image(user, files, file_field_name='file', api_request=False):
    response_data = {'is_success': False, 'message': ''}
    unique_filename = uuid.uuid4()

    try:
        file_name = files[file_field_name].name
        extension = file_name.rsplit('.', 1)[1]
        unique_filename = "{0}.{1}".format(unique_filename,
                                           extension)
        file_path = handle_uploaded_file(files[file_field_name], unique_filename)
        response_data = upload_image(files, file_field_name, file_path)
        if not response_data['is_success']:
            return response_data
        user.profile.extra_profile_img.create(profile_img="skigit/profile/%s" % unique_filename)

        if api_request:
            new_profile_image = user.profile.extra_profile_img.latest('id')
            response_data.update({"is_success": True,
                                  "message": "The profile image is uploaded successfully.",
                                  "data": {
                                      "id": new_profile_image.id,
                                      "new_image": '{0}'.format(api_request_images(new_profile_image.profile_img))
                                  }})
        else:
            response_data.update(
                {'is_success': True, 'message': "{0}skigit/profile/{1}".format(settings.MEDIA_URL,
                                                                                       unique_filename),
                 "unique_filename": str(unique_filename)})
    except Exception as exc:
        logger.error("Extra profile image is not uploaded: ", exc)
        response_data.update({"is_success": False,
                              "message": "Extra profile image is not uploaded successfully. Please try again."})
    return response_data


def upload_business_logo(user, files, file_field_name='file', api_request=False):
    response_data = {'is_success': False, 'message': ''}
    unique_filename = uuid.uuid4()

    try:
        file_name = files[file_field_name].name
        extension = file_name.rsplit('.', 1)[1]
        unique_filename = "{0}.{1}".format(unique_filename,
                                           extension)
        file_path = handle_uploaded_business_logo(files[file_field_name], unique_filename)
        response_data = upload_image(files, file_field_name, file_path)
        if not response_data['is_success']:
            return response_data
        logo = user.profile.logo_img.create(logo="skigit/logo/%s" % unique_filename)
        # record monthly logo invoice
        try:
            updateMonthlyLogoInvoice(user, logo)
        except:
            return response_data

        if api_request:
            new_image = user.profile.logo_img.latest('id')
            response_data.update({"is_success": True,
                                  "message": "The business logo is uploaded successfully.",
                                  "data": {
                                      "id": new_image.id,
                                      "new_image": '{0}'.format(api_request_images(new_image.logo))
                                  }})
        else:
            response_data.update({"is_success": True, "message": "{0}skigit/logo/{1}".format(settings.MEDIA_URL,
                                                                                             unique_filename),
                                  "unique_filename": str(unique_filename)})
    except Exception as exc:
        logger.error("Business logo is not uploaded: ", exc)
        response_data.update({"is_success": False,
                              "message": "Business logo is not uploaded successfully. Please try again."})
    return response_data

def upload_business_doc(user, img_url, files, file_field_name='file[0]'):
    response_data = {'is_success': False, 'message': ''}
    unique_filename = uuid.uuid4()

    try:
        file_name = files[file_field_name].name
        extension = file_name.split('.', 1)[-1]
        unique_filename = "{0}.{1}".format(unique_filename, extension)
        """ 
        response_data = validate_doc_type(files, file_field_name)

        if not response_data['is_success']:
            return response_data
        """
        file_path = handle_uploaded_business_doc(files[file_field_name], unique_filename)
        #store database to do.
        doc = user.profile.business_doc.create(doc=file_path)

        response_data.update({"is_success": True, "message":"Business Documentation is uploaded successfully.", "img":img_url, "alt":file_path})
    except Exception as exc:
        logger.error("Business Documentation is not uploaded: ", exc)
        response_data.update({"is_success": False, "message":"Business Documentation is not uploaded successfully. Please try again."})

    return response_data

def upload_coupon_image(user, files, file_field_name='file', api_request=False):
    context = {'is_success': False,
               'message': ''}

    try:
        filepath = handle_uploaded_coupan_img(files[file_field_name], files[file_field_name].name)
        response_data = upload_image(files, file_field_name, filepath)
        context = response_data
        if response_data['is_success']:
            profile = Profile.objects.get(user=user)
            profile.coupan_image = "skigit/coupan/%s" % files[file_field_name].name
            profile.save()
            if api_request:
                context.update({'is_success': True,
                                'message': 'The coupon image is uploaded successfully.',
                                'data': {
                                    'new_image': '{0}{1}'.format(settings.MEDIA_URL, profile.coupan_image)
                                }})
            else:
                context.update({"is_success": True,
                                "message": "{0}skigit/coupan/{1}".format(settings.MEDIA_URL,files[file_field_name].name)})
    except Exception as exc:
        logger.error("Upload Coupon image is not uploaded:", exc)
        context.update({'is_success': False,
                        'message': 'The coupon image is not uploaded successfully. Please try again.'})
    return context


def get_video_detail_obj(param):
    video_detail = get_object_or_None(VideoDetail, **param)
    video = video_detail.skigit_id
    return video, video_detail


def make_like(video_detail_id, user_id):
    video, video_detail = get_video_detail_obj({'id': video_detail_id})
    result = {}

    if video_detail and video:
        video_id = video.id
        if Like.objects.filter(skigit__id=video_id, user_id=user_id).exists():
            like = Like.objects.filter(skigit__id=video_id, user_id=user_id).update(status=True)
            is_success = True
            message = "Skigit Liked"
        else:
            Like.objects.create(skigit=video, user=User.objects.get(id=user_id), status=True, is_read=False)
            message = "new entry in like table"
            is_success = True
            like = 1

        if not (user_id == video.user.id):
            if (notification_settings(video.user.id, 'like_notify')) == True:
                if not Notification.objects.filter(msg_type='like', skigit_id=video.id,
                                                   user=video.user, from_user__id=user_id).exists():
                    Notification.objects.create(msg_type='like', skigit_id=video.id,
                                                user=video.user, from_user=get_object_or_None(User, id=user_id),
                                                message='skigit_like')
                else:
                    Notification.objects.filter(msg_type='like', skigit_id=video.id,
                                                user=video.user, from_user__id=user_id
                                                ).update(is_read=False, message='skigit_updated_like')
    else:
        message = "error"
        is_success = False
        like = 0
    result.update(message=message,
                  is_success=is_success,
                  like=like)
    return result


def make_unlike(video_detail_id, user_id):
    result = {}
    video, video_detail = get_video_detail_obj({'id': video_detail_id})

    if video_detail and video:
        video_id = video.id
        unlike = Like.objects.filter(skigit__id=video_id, user_id=user_id).update(status=False)
        if Notification.objects.filter(msg_type='like', skigit_id=video.id,
                                       user=video.user, from_user__id=user_id).exists():
            Notification.objects.filter(msg_type='like',
                                        skigit_id=video.id,
                                        user=video.user,
                                        from_user__id=user_id
                                        ).update(msg_type='unlike_deleted',
                                                 message='Unlike', is_view=False,
                                                 is_active=False, is_read=True)
        is_success = True
        message = ""
    else:
        is_success = False
        message = "error"
        unlike = 0
    result.update(message=message,
                  is_success=is_success,
                  unlike=unlike)
    return result


def make_follow(follow_id, user_id, video_detail_id=None):
    result = {}
    cur_user = get_object_or_None(User, id=user_id)
    follow_user = get_object_or_None(User, id=follow_id)
    follow_msg = 'Congratulations {} Started following you.'.format(cur_user.username)
    if video_detail_id:
        video, video_detail = get_video_detail_obj({'id': video_detail_id})
        video_id = video.id
    else:
        video_id = None
    is_success = True

    try:
        if Follow.objects.filter(follow=follow_id, user__id=user_id).exists():
            is_follow = Follow.objects.filter(follow=follow_id, user_id=user_id).update(status=True)
            message = "Following Skigit"
        else:
            Follow.objects.create(follow=follow_user, user=cur_user, status=True)
            message = "new entry in follow table"
            is_success = True
            is_follow = True

        if (notification_settings(follow_user.id, 'follow_un_follow_notify') and not
        user_id == follow_id):
            if not Notification.objects.filter(msg_type='follow', user=follow_user,
                                               from_user__id=user_id).exists():
                notification = Notification.objects.create(msg_type='follow', user=follow_user,
                                                           from_user=cur_user,
                                                           message=follow_msg)
                if video_id:
                    notification.skigit_id = video_id
                    notification.save()
            else:
                notifications = Notification.objects.filter(msg_type='follow', user=follow_user,
                                                            from_user__id=user_id)
                notifications.update(is_read=False, message=follow_msg)
                if video_id:
                    notifications.update(skigit_id=video_id)
    except Exception as exc:
        is_success = False
        is_follow = False
        message = "The user is not followed successfully. Please try later."
        logger.error("Skigit Views: make_follow:", exc)
    result.update(message=message,
                  is_success=is_success,
                  is_follow=is_follow)
    return result


def make_unfollow(follow_id, user_id):
    result = {}
    user = get_object_or_None(User, id=user_id)
    is_found = get_object_or_None(User, id=follow_id)

    is_follow = Follow.objects.filter(user=user.id, follow=follow_id,
                                      status=True).update(status=False)
    if not (user == is_found):
        if Notification.objects.filter(msg_type='follow', user=is_found, from_user=user).exists():
            unfollow_msg = "{0} ended following you.".format(user.username)
            Notification.objects.filter(msg_type='follow', user=is_found,
                                        from_user=user).update(msg_type='unfollow_deleted',
                                                               is_read=True, is_active=False,
                                                               is_view=True)
            if notification_settings(is_found.id, 'follow_un_follow_notify'):
                Notification.objects.create(msg_type='unfollow',
                                            user=is_found, from_user=user, message=unfollow_msg)
    result.update(is_success=True,
                  message="Un Follow User Sussessfully",
                  is_follow=is_follow)
    return result


def make_favourite(video_detail_id, user_id):
    result = {}
    user = get_object_or_None(User, pk=user_id)
    video, video_detail = get_video_detail_obj({'id': video_detail_id})
    video_id = video.id

    if Favorite.objects.filter(skigit__id=video_id, user_id=user.id).exists():
        is_fav = Favorite.objects.filter(skigit__id=video_id, user_id=user.id).update(status=1)
        is_success = True
        message = "Favorite Skigit"
    else:
        Favorite.objects.create(skigit=video, user=user, status=1)
        message = "new entry in favorite table"
        is_success = True
        is_fav = 1
    result.update(is_success=is_success,
                  message=message,
                  is_fav=is_fav)
    return result


def make_unfavourite(video_detail_id, user_id):
    result = {}
    video, video_detail = get_video_detail_obj({'id': video_detail_id})

    is_fav = Favorite.objects.filter(skigit__id=video.id, user_id=user_id).update(status=0)
    result.update(is_success=True,
                  message="Unfavoured skigit",
                  is_fav=is_fav)
    return result


def manage_video_statistics(video_detail_id):
    result = {}
    video, video_detail = get_video_detail_obj({'id': video_detail_id})
    video_id = video.id

    try:
        like_count = Like.objects.filter(skigit__id=video_id, status=True).count()
    except:
        like_count = 0
    try:
        fav_count = Favorite.objects.filter(skigit__id=video_id, status=1, is_active=True).count()
    except:
        fav_count = 0
    try:
        plug_count = VideoDetail.objects.filter(plugged_skigit__id=video_id, is_plugged=True, status=1).count()
    except:
        plug_count = 0
    try:
        if VideoDetail.objects.filter(skigit_id__id=video_id, status=1).exists():
            vid = VideoDetail.objects.get(skigit_id__id=video_id, status=1)
            view_count = vid.view_count
        else:
            view_count = 0
    except:
        view_count = 0
    try:
        if Share.objects.filter(skigit_id=video_id, is_active=True).exists():
            share_count = Share.objects.filter(skigit_id=video_id, is_active=True).count()
        else:
            share_count = 0
    except:
        share_count = 0

    result.update(like_count=like_count,
                  fav_count=fav_count,
                  plug_count=plug_count,
                  view_count=view_count,
                  share_count=share_count,
                  is_success=True,
                  message='Statistic Count.')
    return result


def manage_flag_video(video_detail_id, user_id, flag_reason_id):
    result = {}
    video, video_detail = get_video_detail_obj({'id': video_detail_id})

    if flag_reason_id is not None:
        is_success = True

        try:
            InappropriateSkigit(skigit=video_detail,
                                reported_user=get_object_or_None(User, pk=user_id),
                                reason=get_object_or_None(InappropriateSkigitReason, pk=flag_reason_id),
                                action='0',
                                status='2').save()
            message = "Your request will be reviewed!"
        except Exception as exc:
            logger.error("Skigit:Views: manage_flag_video:", exc)
            is_success = False
            message = "Invalid details found!"
    else:
        is_success = False
        message = "Please select a reason!"
    result.update(is_success=is_success,
                  message=message)
    return result


def manage_share_video(user_id, time_zone, video_id, friend_list):
    response_data = {}
    user = get_object_or_None(User, pk=user_id)

    for f_id in friend_list:
        if User.objects.filter(id=f_id).exists():
            user_obj = User.objects.get(id=f_id)
            share_obj = Share.objects.create(user=user, to_user=user_obj, skigit_id_id=video_id)
            if VideoDetail.objects.filter(id=int(video_id)).exists():
                video = VideoDetail.objects.get(id=int(video_id))
                business_share_invoice(user_id, video.skigit_id.id)
                mail_id = user_obj.email

                EmailTemplate.send(
                    template_key="shared_an_awesome_skigit",
                    emails=mail_id,
                    context={
                        "username": user.username,
                        "skigit_id": video_id,
                        "title": video.title,
                        "why_rocks": video.why_rocks,
                        "host": ''.join(settings.HOST)[:-1]
                    })

                f_nt_message = " You are on the Radar! {0} has shared the awesome Skigit {1} with you! ".format(
                    user.username,
                    video.title)
                if notification_settings(user_obj.id, 'share_notify'):
                    if not Notification.objects.filter(msg_type='share', user=user_obj,
                                                       skigit_id=video.skigit_id.id,
                                                       from_user=user).exists():
                        Notification.objects.create(user=user_obj, from_user=user,
                                                    skigit_id=video.skigit_id.id,
                                                    msg_type='share',
                                                    message=f_nt_message)
                    else:
                        Notification.objects.filter(user=user_obj, skigit_id=video.skigit_id.id,
                                                    from_user=user,
                                                    msg_type='share').update(msg_type='share_old', is_view=True,
                                                                             is_active=False, is_read=True)
                        Notification.objects.filter(user=user_obj, from_user=user,
                                                    skigit_id=video.skigit_id.id, msg_type='share_old').delete()
                        Notification.objects.create(user=user_obj, from_user=user,
                                                    skigit_id=video.skigit_id.id, msg_type='share',
                                                    message=f_nt_message)
    response_data['is_success'] = True
    response_data['message'] = 'Thanks for sharing!'
    response_data['date'] = get_time_delta(datetime.utcnow(), time_zone)
    return response_data


def manage_video_search(data):
    search_text = data.get('search_text', '')
    vid = []
    sort_by = data.get('sort_by', 'updated_date')
    order_by = data.get('order_by', 'desc')

    ordering = '-{0}'.format(sort_by) if order_by == 'desc' else '{0}'.format(sort_by)

    if search_text:
        profile = Profile.objects.filter(Q(company_title__icontains=search_text))
        if profile:
            for p in profile:
                vid = VideoDetail.objects.select_related(
                    'skigit_id').filter(Q(skigit_id__user__id=p.id) |
                                        Q(skigit_id__user__username__icontains=search_text) |
                                        Q(title__icontains=search_text), status=1, is_active=True
                                        ).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by(ordering)
        else:
            vid = VideoDetail.objects.select_related(
                'skigit_id').filter(Q(title__icontains=search_text) |
                                    Q(skigit_id__user__username__icontains=search_text),
                                    status=1, is_active=True).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by(ordering)
    else:
        vid = VideoDetail.objects.select_related('skigit_id').filter(status=1, is_active=True).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by(ordering)
    return vid


def manage_share_video_to_email(user_id, video_id, email_list):
    response_data = {'is_success': False,
                     'message': 'Skigit is not shared successfully. Please try again later.'}
    user = get_object_or_None(User, id=user_id)
    video = VideoDetail.objects.filter(id=int(video_id)).exists()

    if video.exists():
        video = video[0]
        for mail_id in email_list:
            Share.objects.create(user=user, to_user=None, skigit_id_id=video_id)
            EmailTemplate.send(
                template_key="shared_an_awesome_skigit_2",
                emails=mail_id.strip(),
                context={
                    "username": user.username,
                    "skigit_id": video_id,
                    "title": video.title,
                    "why_rocks": video.why_rocks,
                    "host": ''.join(settings.HOST)[:-1]
                })
        response_data['is_success'] = True
        response_data['message'] = 'Skigit is shared successfully'
    return response_data


def manage_upload_video(user_id, data, files=None, plugin_upload=False):
    if data.get('file_on_server', '') or files:
        response_data = manage_direct_upload_video(user_id, data, files=files, plugin_upload=plugin_upload)
    else:
        response_data = manage_link_upload_video(user_id, data, plugin_upload=plugin_upload)
    return response_data


def manage_plugin_upload_video(user_id, data, files=None):
    response_data = manage_upload_video(user_id, data, files=files, plugin_upload=True)
    if response_data['is_success']:
        user = get_object_or_None(User, id=user_id)
        video_detail = get_object_or_None(VideoDetail, id=data.get('plug_id'))
        plugged_video = get_object_or_None(Video, id=video_detail.skigit_id.id)
        plugged_user = video_detail.skigit_id.user
        plug_videos = Plugged(skigit=plugged_video,
                              user=user,
                              plugged=plugged_user)
        plug_videos.save()

    return response_data


def manage_link_upload_video(user_id, data, plugin_upload=False):
    response_data = {}
    title = data.get("title", '')
    title = string.capwords(title)  # Capitalize first letter of each word
    video_link = str(data.get('video_link', ''))

    res = requests.get(video_link)
    made_by = data.get('made_by', '')
    made_by_option = data.get('made_by_option', '')

    if not made_by and not made_by_option:
        response_data['is_success'] = False
        response_data['message'] = "You must either select a name from dropdown list or if the name does not exist, \
                                    enter the appropriate name in the text entry box"
        return response_data
    if not video_link:
        response_data['is_success'] = False
        response_data['message'] = "Video Link - This field is required"
        return response_data

    if video_link and not (video_link.count("youtube") or video_link.count("youtu.be")):
        response_data['is_success'] = False
        response_data['message'] = "Your link is not a valid YouTube link. Check the link and try again"
        return response_data
    
    # check for youtube playlist link address
    if 'list=' in video_link:
      response_data['is_success'] = False
      response_data['message'] = "You have uploaded an incorrect link. Make sure you copy and paste the YouTube SHARE link only. Please try again."
      return response_data
    
    if ("Video unavailable" in res.text):
        response_data['is_success'] = False
        response_data[
            'message'] = "Your Link is in the correct format but is unavailable on YouTube. Please contact YouTube or try another link to upload."
        return response_data

    if VideoDetail.objects.filter(title=title).exists():
        response_data['is_success'] = False
        response_data['message'] = "Title is already used. Please enter different one."
        return response_data

    url_parts = video_link.split("/")
    url_parts.reverse()
    url_parts1 = url_parts[0].split("?v=")
    url_parts1.reverse()
    video_id = url_parts1[0]
    swf_url = 'https://www.youtube.com/embed/' + video_id + \
              '?modestbranding=1&showinfo=0&autoplay=0&autohide=1&rel=0&wmode=transparent'
    cur_user = get_object_or_None(User, id=user_id)

    if Video.objects.filter(video_id=video_id).exists():
        response_data['is_success'] = False
        response_data[
            'message'] = "&#x2718; We're sorry but your video failed to upload because it was previously posted. Please try again. " \
                         "link"
        return response_data
    else:
        UploadedVideoLink.objects.create(video_link=video_link)

        # save video_id to video instance
        video = Video(user=cur_user,
                      video_id=video_id,
                      title=title,
                      youtube_url=video_link,
                      swf_url=swf_url,
                      created_by=cur_user)
        skigit_form = VideoDetail()
        skigit_form.title = title
        category_value = data.get('category', '')
        sub_category_value = data.get('subject_category', '')
        if category_value:
            category = Category.objects.get(id=category_value)
            skigit_form.category = category
        if sub_category_value:
            subject_category = SubjectCategory.objects.get(id=sub_category_value)
            skigit_form.subject_category = subject_category
        add_logo = data.get('add_logo', 0)
        skigit_form.add_logo = add_logo
        receive_donate_sperk = data.get('receive_donate_sperk', 0)
        skigit_form.receive_donate_sperk = receive_donate_sperk
        skigit_form.why_rocks = data.get('why_rocks', '')
        made_by = made_by
        made_by = made_by if made_by not in ['null'] else None
        if made_by:
            user = User.objects.get(id=int(made_by))
            skigit_form.made_by = user
            skigit_form.business_user = user
        if made_by_option:
            skigit_form.made_by_option = made_by_option
        select_logo = data.get("select_logo", '')
        if data.get("add_logo", '') == '1' and \
                (not select_logo == 'undefined' and not select_logo == '') and \
                BusinessLogo.objects.filter(id=select_logo).exists():
            busness_logo = BusinessLogo.objects.get(id=select_logo)
            skigit_form.business_logo = busness_logo
            skigit_form.is_sperk = True
            if receive_donate_sperk != '' and receive_donate_sperk != 'undefined':
                if int(receive_donate_sperk) == 2:
                    donate = get_object_or_None(Donation, id=int(data.get('donate_skigit', 0)))
                    if donate:
                        skigit_form.donate_skigit = donate

                # check if bussiness user has offered incentive,
                # also if user selected one of Receieve or Donate option
                if made_by and user.profile.incentive == 1 and int(receive_donate_sperk) in [1, 2]:
                    incentive = Incentive(amount=user.profile.incetive_val,
                                          user=user,
                                          sperk_type=int(receive_donate_sperk),
                                          title='Incentive for {} skigit'.format(data.get("title", '')),
                                          is_active=False,
                                          billing_month=datetime.now().date())
                    incentive.save()
                    skigit_form.incentive = incentive
        skigit_form.bought_at = data.get("bought_at", "")
        skigit_form.why_rocks = data.get("why_rocks", "")
        if receive_donate_sperk == '' or receive_donate_sperk == 'undefined':
            skigit_form.receive_donate_sperk = 0

        video.save1()
        try:
            skigit_form.skigit_id = video
            skigit_form.share_skigit = video
            if plugin_upload:
                video_detail = get_object_or_None(VideoDetail, id=data.get('plug_id', ''))
                plugged_video = get_object_or_None(Video, id=video_detail.skigit_id.id)
                skigit_form.is_plugged = True
                skigit_form.plugged_skigit = plugged_video
                skigit_form.share_skigit = video

            skigit_form.created_by = cur_user
            skigit_form.view_count = 0
            skigit_form.save()
        except Exception as exc:
            # delete video link from database if the upload was not successful
            video.delete()

        Notification.objects.create(msg_type='video_uploaded', skigit_id=skigit_form.skigit_id.id,
                                    user=skigit_form.skigit_id.user, from_user=cur_user,
                                    message="Your video has been successfully uploaded. You'll be notified when posted")

        if config.VIDEOS_AUTO_APPROVAL:
            video_url = 'https://www.youtube.com/oembed?url={}&format=json'.format(video_link)
            video_data = requests.get(video_url)
            if video_data.status_code in [200]:
                approve_video(skigit_form, admin_user=cur_user)
            else:
                unapprove_video(skigit_form, template_key='skigit_rejected_youtube_unavailable', request_user=cur_user)

        response_data['is_success'] = True
        response_data[
            'message'] = "Your video was successfully uploaded and you will be notified when posted."
        return response_data


def manage_direct_upload_video(user_id, data, files=None, plugin_upload=False):
    title = data.get("title", '')
    title = string.capwords(title)  # Capitalize first letter of each word
    response_data = {}
    made_by = data.get('made_by', '')
    made_by_option = data.get('made_by_option', '')

    if not made_by and not made_by_option:
        response_data['is_success'] = False
        response_data['message'] = "You must either select a name from dropdown list or if the name does not exist, \
                                    enter the appropriate name in the text entry box"
        return response_data

    if VideoDetail.objects.filter(title=title).exists():
        response_data['is_success'] = False
        response_data['message'] = "Title is already used. Please enter different one."
        return response_data

    form = YoutubeDirectUploadForm(data, files)
    if form.is_valid():
        uploaded_video = form.save()

        # file size in mbs
        file_size = math.ceil(uploaded_video.file_on_server.size / (1024 * 1024))

        # file size is too large
        if file_size > 100:
            response_data['is_success'] = False
            response_data['message'] = "Too large file - Max upload size is 100MB"
            return response_data

        crf = '33'
        if file_size >= 60 and file_size <= 100:
            crf = '35'

        made_by = made_by if made_by not in ['null'] else None

        # pass data to celery task
        video_compression_and_upload.delay({
        #video_compression_and_upload({
            "user_id": user_id,
            "uploaded_video_id": uploaded_video.id,
            "crf": crf,
            "title": title,
            "plugin_upload": plugin_upload,
            "why_rocks": data.get('why_rocks', ''),
            "category": data.get('category', ''),
            "subject_category": data.get('subject_category', ''),
            "add_logo": data.get('add_logo', 0),
            "receive_donate_sperk": data.get('receive_donate_sperk', 0),
            "made_by": made_by,
            "made_by_option": made_by_option,
            "select_logo": data.get('select_logo', ''),
            "donate_skigit": data.get('donate_skigit', 0),
            "bought_at": data.get('bought_at', ''),
            "plug_id": data.get('plug_id', ''),
        })

        response_data['is_success'] = True
        response_data[
            'message'] = "Congratulations! Your video was successfully uploaded and you will be notified when posted."

    else:
        response_data['is_success'] = False
        response_data['message'] = "Please upload video or video link."
    return response_data


def manage_sperk(user_id, api_request=False):
    incentive_detail = None
    all_business_logo = ""
    data = {'incentive_detail': incentive_detail, 'all_business_logo': all_business_logo}

    if not user_id:
        return data

    usr = get_object_or_None(User, id=int(user_id))
    if usr:
        profile = Profile.objects.filter(user=usr)
        all_business_logo = []
        if profile.exists():
            if profile.filter(incentive=1).exists():
                incentive_detail = usr.profile.skigit_incentive
                if not incentive_detail:
                    incentive_detail = None
    
            # get business logo
            profile = usr.profile
            if profile.is_completed['status']:
                logos = profile.logo_img.filter(is_deleted=False)
                if logos.exists():
                    if api_request:
                        logo_serializer = BusinessLogoSerializer(logos, many=True)
                        all_business_logo = logo_serializer.data
                    else:
                        all_business_logo= [[l_obj.id, l_obj.logo.url] for l_obj in logos]
        data.update(incentive_detail=incentive_detail, all_business_logo=all_business_logo)
    else:
        data.update(incentive_detail=None, all_business_logo=[])
    return data


def get_sperk_profile_detail(cur_user_id, sperk_user_id):
    context = {}
    response_data = {'is_success': True,
                     'message': '',
                     'context': context}
    profile = get_object_or_None(Profile, user__id=sperk_user_id)
    profile_serializer = ProfileBusinessSerializer(profile)

    try:
        request_user = get_object_or_None(User, id=sperk_user_id, is_active=True)
    except ObjectDoesNotExist:
        response_data.update(is_success=False,
                             message='Sorry, Your Request User Not Found.')
        return response_data

    if not request_user.profile.is_completed['status']:
        response_data.update(is_success=False,
                             message='Sorry, Your request user profile is not active.')
        return response_data

    try:
        logos = profile.logo_img.filter(is_deleted=False)
        business_logo_serializer = BusinessLogoSerializer(logos, many=True)

        extra_profile_images = profile.extra_profile_img.all()
        extra_profile_images_serializer = ExtraProfileImageSerializer(extra_profile_images, many=True)
        embed_skigit_exist = True if Embed.objects.filter(to_user=request_user, is_embed=True).exists() else False
        profile_url, created = ProfileUrl.objects.get_or_create(user__id=sperk_user_id)
        profile_urls = get_company_urls(profile_url)

        context.update(profile=profile_serializer.data,
                       company_links=profile_urls,
                       business_logos=business_logo_serializer.data,
                       extra_profile_images=extra_profile_images_serializer.data,
                       embedded_videos=embed_skigit_exist)
    except Exception as exc:
        logger.error("Get sperk Profile detail throws error: ", exc)
        response_data.update(is_success=False,
                             message='The sperk detail is not loaded. Please try again later.')

    return response_data


@method_decorator(payment_required, name='dispatch')
@method_decorator(require_filled_profile, name='dispatch')
class AwesomeThings(TemplateView):
    def get(self, request):
        context = {}

        awesome_cat = SubjectCategory.objects.filter(
            is_active=True
        ).order_by(
            'sub_cat_name'
        )
        if awesome_cat:
            context.update({'awesome_cat': awesome_cat})
        return render(request, "category/awesome_category.html", context)


# @method_decorator(login_required(login_url='/login'), name='dispatch')
@method_decorator(payment_required, name='dispatch')
@method_decorator(require_filled_profile, name='dispatch')
class AwesomeThingsCategory(TemplateView):
    def get(self, request, sub_cat_slug=None):
        page_template = 'includes/skigit_list.html'
        template = 'category/skigit_plugged_into.html'

        user = vid = category = user_profile = video_likes = category_current = None
        like_dict = []

        try:
            category_current = SubjectCategory.objects.get(
                sub_cat_slug=sub_cat_slug, is_active=True)
            vid = VideoDetail.objects.select_related('skigit_id').filter(
                subject_category=category_current, status=1, is_active=True).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by(
                '-updated_date')

        except ObjectDoesNotExist:
            messages.error(request, 'Your Requested Awesome things not found...!!!')
            return HttpResponseRedirect("/")

        like_skigit = []
        if request.user.is_authenticated:
            video_likes = Like.objects.filter(user_id=request.user.id, status=True)
            for likes in video_likes:
                like_skigit.append(likes.skigit_id)

        context = {
            'video_detail': vid,
            'category_current': category_current,
            'user': user,
            'user_profile': user_profile,
            'video_likes': like_skigit,
            'video_type': 'sub_cat',
        }

        if request.is_ajax():
            template = page_template
        return render(request, template, context)


class Sharing(TemplateView):
    def get(self, request, pk):
        template = 'includes/friends_share.html'

        friend_list = []
        if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1).exists():
            f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1)
            from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user', flat=True).distinct()
            to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user', flat=True).distinct()
            fr_list = list(merge(from_user_list, to_user_list))
            friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')

            for friends in friends_detail:
                if friends.profile_img:
                    # l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                    l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
                else:
                    l_img = "{0}{1}".format(settings.STATIC_HOST_URL, 'images/noimage_user.jpg')
                friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                    'name': friends.user.get_full_name(), 'image': l_img})

        vid = VideoDetail.objects.get(id=pk)

        context = {
            'friend_list': friend_list,
            'vid': vid
        }

        return render(request, template, context)


class SkigitData(SkigitBaseView):
    def get(self, request, pk, extra_context=None, *args, **kwargs):
        template = 'includes/skigit_popup.html'
        kwargs.update(skigit_id=pk)
        context_extra = self.get_context_data(**kwargs)

        video_liked = False
        video_favorite = False
        video_follow = False
        skigit_user_profile_default_logo = ''
        user = request.user
        is_anonymous = user.is_anonymous

        skigit = VideoDetail.objects.filter(id=pk, status=1).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        )
        if not skigit.exists():
            return HttpResponseRedirect("/?id=%s" % pk)
        else:
            skigit = skigit.first()

        embed_skigit = EmbedInvoice.objects.filter(skigit_user__id=skigit.skigit_id.user.id, user__id=user.id,
                                                   embed_ski=skigit).exists()
        if is_anonymous:
            is_business = False
        else:
            user_type = get_user_type(user)
            is_business = True if user_type == 'business' else False

        count_i_plugged_into = 0

        all_reason = InappropriateSkigitReason.objects.values('id', 'reason_title')

        if not is_anonymous:
            count_i_plugged_into = VideoDetail.objects.filter(plugged_skigit__user=user, status=1,
                                                              is_plugged=True).count()
            video_liked = Like.objects.filter(user_id=user.id, skigit_id__id=skigit.skigit_id.id,
                                              status=True).exists()

            video_favorite = Favorite.objects.filter(user_id=user.id,
                                                     status=1, skigit_id__id=skigit.skigit_id.id).exists()
            video_follow = Follow.objects.filter(user=user.id, status=True,
                                                 follow__id=skigit.skigit_id.user_id).exists()

        if skigit.made_by:
            skigit_user_profile = skigit.made_by.profile
            skigit_business_logo = skigit.business_logo
            if (skigit_business_logo and skigit_business_logo.is_deleted) or not skigit_business_logo:
                us_profile_logos = skigit_user_profile.logo_img.filter(is_deleted=False)
                skigit_user_profile_default_logo = us_profile_logos[0] if us_profile_logos.exists() else ''
            elif skigit_business_logo:
                skigit_user_profile_default_logo = skigit_business_logo

        skigit_thumbnails = skigit.skigit_id.thumbnails.all()
        skigit_thumbnail = skigit_thumbnails[0].get_absolute_url if skigit_thumbnails.exists() else ''
        video_share_url = context_extra['meta'].image

        context = {
            "skigit": skigit,
            "video_liked": video_liked,
            "embed_skigit_vid": embed_skigit,
            "all_reason": all_reason,
            "video_favorite": video_favorite,
            "video_favorite_count": video_favorite,
            "count_i_plugged_into": count_i_plugged_into,
            "default_logo": skigit_user_profile_default_logo,
            "video_follow": video_follow,
            "is_business": is_business,
            "video_share_url": video_share_url,
            "skigit_category": safe(skigit.category),
            "is_anonymous": is_anonymous,
            "skigit_user_id": skigit.skigit_id.user.id,
            "skigit_thumbnail": skigit_thumbnail,
            "facebook_app_id": settings.FACEBOOK_APP_ID,
        }
        context.update(context_extra)
        return render(request, template, context)

def recommended_skigits(request, skigit_id):
    cur_user = request.user
    skigit = get_object_or_None(VideoDetail, pk=skigit_id, status=1)
    related_user_list = get_related_users(cur_user.id, skigit.skigit_id.user.id)
    other_videos = VideoDetail.objects.filter(status=1, is_active=True).exclude(id=skigit_id).distinct()
    other_videos = cache.get_or_set('all_sub_cat_skigits', other_videos.select_related('skigit_id').filter(
        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True))).distinct()
    other_videos = other_videos.exclude(id=skigit_id)
    page = request.GET.get('page',1)
    is_anonymous = cur_user.is_anonymous
    if is_anonymous or not related_user_list:
        all_sub_cat_skigits = other_videos.filter(
            subject_category=skigit.subject_category).order_by('?')
    else:
        all_sub_cat_skigits = other_videos.filter(Q(subject_category=skigit.subject_category) |
                                                  Q(skigit_id__user__in=related_user_list)).order_by('?')
        if not all_sub_cat_skigits.exists():
            all_sub_cat_skigits = other_videos.filter(
                subject_category=skigit.subject_category).order_by('?')
        if not all_sub_cat_skigits.exists():
            all_sub_cat_skigits = other_videos.filter(
                skigit_id__user__in=related_user_list).order_by('?')
    if not all_sub_cat_skigits:
        all_sub_cat_skigits = other_videos
    
    paginator = Paginator(all_sub_cat_skigits, 10)
    all_sub_cat_skigits = paginator.page(page)
    return render(request, 'includes/recommended_skigits.html', {'all_sub_cat_skigits': all_sub_cat_skigits})


class SkigitPluginMap(SkigitBaseView):
    def get(self, request, pk, extra_context=None, *args, **kwargs):
        template = 'includes/plugin_skigit_list.html'
        kwargs.update(skigit_id=pk)
        context = self.get_context_data(**kwargs)
        videos_list = fetch_plugins_with_position(pk)
        # we need map plugins to be attached at specific location
        positions = []
        if len(videos_list) == 1:
            positions = [1]
        elif len(videos_list) == 2:
            positions = [7, 8]
        elif len(videos_list) == 3:
            positions = [1, 7, 8]
        elif len(videos_list) == 4:
            positions = [7, 8, 5, 6]
        elif len(videos_list) == 5:
            positions = [1, 7, 8, 5, 6]
        elif len(videos_list) == 6:
            positions = [1, 7, 8, 2, 5, 6]
        elif len(videos_list) == 7:
            positions = [1, 7, 8, 5, 6, 3, 4]
        elif len(videos_list) == 8:
            positions = [1, 7, 8, 5, 6, 3, 4, 2]

        context.update({
            'videos_list': videos_list,
            'skigit_id': pk,
            'positions': positions,
        })

        return render(request, template, context)


# TODO:move to another file
def getSwfURL(video_id):
    url = 'https://www.youtube.com/embed/%s' \
          '?modestbranding=1&showinfo=0&autoplay=0&autohide=1&rel=0&wmode=transparent' % (video_id)
    return url


def getYoutubeURL(video_id):
    url = 'https://www.youtube.com/watch?v=%s' % video_id
    return url


@method_decorator(login_required(login_url='/login'), name="dispatch")
@method_decorator(payment_required, name="dispatch")
@method_decorator(require_filled_profile, name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class DirectUpload(TemplateView):
    """ PRIMARY SKIGIT: Direct video upload method
    """

    def get(self, request, *args, **kwargs):
        form = YoutubeDirectUploadForm()
        form1 = SkigitUploadForm()
        form2 = YoutubeLinkUploadForm()
        organization_list = Donation.objects.all()
        message = ''
        cur_user = request.user
        canPost = False if is_user_business(cur_user) and not is_verified_business_user(cur_user) else True

        sperk = request.GET.get('sperk', None)
        context = {}
        if sperk:
            user = User.objects.filter(
                groups__name=settings.BUSINESS_USER,
                profile__payment_method__isnull=False,
                profile__payment_email__isnull=False,
                invoice_user__type__in=['PayPalAccount', 'CreditCard'],
                invoice_user__is_deleted=False,
                id=sperk
            ).select_related('profile').first()
            if user:
                logo = user.profile.logo_img.filter(is_deleted=False).first()
                logo_src = "{0}".format(
                    get_thumbnail(logo.logo, "{0}x{1}".format(logo.logo.width, logo.logo.height)).url)
                user_company_name = user.profile.company_title
                business_dropdown_text = "{}:;:{}".format(user_company_name, logo_src)
                context.update(business_dropdown_text=business_dropdown_text,
                               sperk=sperk)
        return render(request, "youtube/yt_direct_upload.html", locals())

    def post(self, request):
        response_data = {}
        try:
            data = request.POST.copy()

            if data.get("title", '') and data.get('category', ''):
                user_id = self.request.user.id
                data.update(user_id=user_id)
                response_data = manage_upload_video(user_id, data, files=request.FILES)
                if 'is_success' in response_data and response_data['is_success']:
                    messages.success(request,
                                     "Congratulations! Your video was successfully uploaded and you will be notified when posted.")
                return JsonResponse(response_data)
        except Exception as exc:
            logger.error("Direct upload is not uploaded: ", exc)
            response_data['is_success'] = False
            response_data['message'] = 'Error into Upload Skigit, Please try again later'
            return JsonResponse(response_data)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_required(login_url='/login'), name="dispatch")
@method_decorator(payment_required, name="dispatch")
@method_decorator(require_filled_profile, name="dispatch")
class LinkUpload(TemplateView):
    """ PRIMARY SKIGIT: link upload method
    """

    def post(self, request):
        response_data = {}
        if request.is_ajax():
            try:
                data = request.POST.copy()
                user_id = self.request.user.id
                data.update(user_id=user_id)
                response_data = manage_upload_video(user_id, data)
                if 'is_success' in response_data and response_data['is_success']:
                    messages.success(request,
                                     "Your video was successfully uploaded and you will be notified when posted.")
                return JsonResponse(response_data)
            except Exception as exc:
                logger.error(exc)
                form1 = SkigitUploadForm()
                form2 = YoutubeLinkUploadForm()
                organization_list = Donation.objects.all()
                response_data['is_success'] = False
                response_data[
                    'message'] = "<span style='font-size:20px;'><i class='glyphicon glyphicon-remove-circle' " \
                                 "style='top: 5px !important;' /></span> Error into Link Skigit, Please try again later"
                return JsonResponse(response_data)
        else:
            form = YoutubeDirectUploadForm()
            form1 = SkigitUploadForm()
            form2 = YoutubeLinkUploadForm()
            organization_list = Donation.objects.all()
            return render(request, "youtube/yt_direct_upload.html", locals())


@method_decorator(login_required(login_url='/login'), name="dispatch")
class YoutubeCheck(View):
    """ PRIMARY SKIGIT: link upload method
    """

    def post(self, request):
        if request.is_ajax():
            response_data = {}
            try:
                data = request.POST.copy()
                res = requests.get(data['youtube_link'])
                response_data['res'] = True if ("Video unavailable" not in res.text) else False
            except Exception as exc:
                pass
            return JsonResponse(response_data)


@method_decorator(login_required(login_url='/login'), name="dispatch")
class GetSperk(View):
    def post(self, request):
        if request.is_ajax():
            user_id = request.POST.get('user_id', None)
            data = manage_sperk(user_id)
            return JsonResponse(data)


@login_required(login_url='/login')
def user_profile_delete(request):
    context = {}
    user = request.user
    context['is_business'] = is_user_business(user)
    form = DeleteProfileForm()
    if request.method == 'POST' and 'user_profile_delete' in request.POST:
        form = DeleteProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            delete_account = data.get('delete_account_confirm', None)
            if delete_account:
                # R.248.1 remove business logo from skigits
                profile = user.profile
                profile.deactivate_reason = data['delete_reason']
                if data['delete_reason_other']:
                    profile.deactivate_other_reason = data['delete_reason_other']
                profile.save()
                delete_user_account(user)
                logout(request)
                messages.success(request, 'Your account deactivated successfully!')
                return HttpResponseRedirect('/')
            else:
                messages.error(request, 'There Is Something Wrong in deactivate')
    else:
        Profile.objects.get_or_create(user=user)

    user_profile = Profile.objects.get(user=user)
    context.update(csrf(request))
    context['user'] = user
    context['can_delete'] = user_invoices_cleared(user)
    context['user_profile'] = user_profile
    context['form'] = form
    return render(request, 'profile/user_profile_delete.html', context)


@login_required(login_url='/login')
def search_business_users(request):
    users_per_page = 10
    users = User.objects.filter(groups__name=settings.BUSINESS_USER,
                                profile__payment_method__isnull=False,
                                profile__payment_email__isnull=False,
                                invoice_user__type__in=['PayPalAccount', 'CreditCard'],
                                invoice_user__is_deleted=False,
                                profile__business_verified=True
                                ).distinct('username')
    data = request.POST
    page = int(data.get('page', 1))
    term = data.get('term', None)
    if term:
        users = users.filter(profile__company_title__icontains=term)

    users = sorted(users, key=lambda i: (i.profile.company_title.lower())) # sort user based on company title
    paginator = Paginator(users, users_per_page)
    users = paginator.page(page)
    if page == 1:
        results = [{
            'id': '',
            'text': 'Select one'
        }]
    else:
        results = []
    duplicateCompanies = {}
    user_companies = [user_company.profile.company_title for user_company in users]
    for user in users:
        logo = user.profile.logo_img.filter(is_deleted=False).first()

        if logo:
            try:
                logo_src = "{0}".format(get_thumbnail(logo.logo, "{0}x{1}".format(logo.logo.width, logo.logo.height), format='PNG').url)
            except:
                logo_src = ""

            user_company_name = user.profile.company_title

            if user_company_name in duplicateCompanies:
                duplicateCompanies[user_company_name] += 1
                # add extension sequential number for same name duplicates
                company_name = "{} - {}".format(user_company_name,
                                                duplicateCompanies[user_company_name])
            else:
                duplicateCompanies[user_company_name] = 1
                # check if duplicate exists
                count = user_companies.count(user_company_name)
                company_name = "{} - {}".format(user_company_name, 1) if count > 1 else "{}".format(user_company_name)

            results.append({
                'id': user.id,
                'text': "{}:;:{}".format(company_name, logo_src)
            })

    return JsonResponse({'results': results,
                         'next_page': True if users.has_next() else False})


@csrf_exempt
@login_required(login_url='/login')
@payment_required
@require_filled_profile
def ajax_skigit_plugin_link(request, plug_id):
    """
        Plug-in : link upload method
    """
    response_data = {}
    if request.is_ajax() and request.method == 'POST':
        try:
            data = request.POST.copy()
            user_id = request.user.id
            data.update(plug_id=plug_id,
                        user_id=user_id)
            response_data = manage_plugin_upload_video(user_id, data)
            if 'is_success' in response_data and response_data['is_success']:
                messages.success(request,
                                 "Your video was successfully uploaded. You will be notified when posted.")
            return JsonResponse(response_data)
        except:
            form1 = SkigitUploadForm()
            form2 = YoutubeLinkUploadForm()
            organization_list = Donation.objects.all()
            response_data['is_success'] = False
            response_data[
                'message'] = "<span style='font-size:20px;'><i class='glyphicon glyphicon-remove-circle' style='top: 5px !important;' /></span> Error into Link Skigit, Please try again later"
            return JsonResponse(response_data)
    else:
        video_detail = VideoDetail.objects.get(id=plug_id)
        username = video_detail.skigit_id.user.username
        skigit_title = video_detail.title
        plug_category = video_detail.category.id
        sub_catogery = video_detail.subject_category.id
        my_aws_by = video_detail.skigit_id.id
        form = YoutubeDirectUploadForm()
        form1 = SkigitUploadForm()
        form2 = YoutubeLinkUploadForm()
        organization_list = Donation.objects.all()
        return render(request, "youtube/yt_skigit_plugin.html", locals())


@csrf_exempt
@login_required(login_url='/login')
@payment_required
@require_filled_profile
def ajax_skigit_plugin_video(request, plug_id):
    """
        Plug-in : direct upload method
    """
    response_data = {}
    if request.method == 'POST':
        try:
            form = YoutubeDirectUploadForm(request.POST, request.FILES)
            form2 = YoutubeLinkUploadForm(request.POST)
            video_detail = VideoDetail.objects.get(id=plug_id)
            username = video_detail.skigit_id.user.username
            plugged_user = video_detail.skigit_id.user
            skigit_title = video_detail.title
            sub_catogery = video_detail.subject_category.sub_cat_name

            if form.is_valid() and request.POST.get("title", '') and request.POST.get('category', ''):
                data = request.POST.copy()
                user_id = request.user.id
                data.update(plug_id=plug_id,
                            user_id=user_id)
                response_data = manage_plugin_upload_video(user_id, data, files=request.FILES)
                if 'is_success' in response_data and response_data['is_success']:
                    messages.success(request,
                                     "Your video was successfully uploaded and you will be notified when posted.")
                return JsonResponse(response_data)
        except:
            form1 = SkigitUploadForm()
            form2 = YoutubeLinkUploadForm()
            organization_list = Donation.objects.all()
            response_data['is_success'] = False
            response_data[
                'message'] = "<span style='font-size:20px;'><i class='glyphicon glyphicon-remove-circle' style='top: 5px !important;' /></span> Error into Link Skigit, Please try again later."
            # video.delete()
            return JsonResponse(response_data)
    else:
        video_detail = VideoDetail.objects.get(id=plug_id)
        username = video_detail.skigit_id.user.username
        skigit_title = video_detail.title
        plug_category = video_detail.category.id
        sub_catogery = video_detail.subject_category.id
        my_aws_by = video_detail.skigit_id.id
        form = YoutubeDirectUploadForm()
        form1 = SkigitUploadForm()
        form2 = YoutubeLinkUploadForm()
        organization_list = Donation.objects.all()
        message = ''
        return render(request, "youtube/yt_direct_upload.html", locals())


def get_user_notification(request):
    response_data = {'is_success': False, 'message': 'Error in get user notification'}
    if request.is_ajax() and request.user.is_authenticated:
        response_data = get_general_notifications_count(request.user.id)
    return JsonResponse(response_data)


@login_required(login_url='/login')
@payment_required
@require_filled_profile
def my_skigits(request, user_id=None, template='category/my_skigits.html',
               page_template='includes/skigit_list.html'):
    user = vid = category = user_profile = video_likes = category_current = None
    like_dict = []
    profile_dic = []
    try:
        category_current = request.user.username
        vid = VideoDetail.objects.select_related('skigit_id').filter(
            skigit_id__user=request.user, status=1, is_active=True).order_by('-updated_date')

    except ObjectDoesNotExist:
        messages.error(request, 'No Skigits found...!!!')
        return HttpResponseRedirect("/")

    video_likes = Like.objects.filter(user_id=request.user.id, status=1)
    like_skigit = []
    for likes in video_likes:
        like_skigit.append(likes.skigit_id)

    context = {
        'video_detail': vid,
        'category_current': category_current,
        'user': user,
        'user_profile': user_profile,
        'video_likes': like_skigit,
        'can_delete': False,
        'my_skigit': True
    }
    if request.is_ajax():
        template = page_template
    return render(request, template, context)


@login_required(login_url='/login')
@payment_required
@require_filled_profile
def my_skigits_view(request, user_id, template='category/skigit_plugged_into.html',
                    page_template='includes/skigit_list.html'):
    user = us_profile = vid = category = user_profile = video_likes = category_current = None

    like_dict = []
    profile_dic = []
    share_dict = []
    plug_dict = []
    ski_share_list = []
    try:
        category_current = request.user.username
        vid = VideoDetail.objects.select_related('skigit_id').filter(
            skigit_id__user=user_id,
            status=True
        ).order_by('-updated_date')

        for vid_profile in vid:
            like_count = Like.objects.filter(skigit=vid_profile.skigit_id, status=True).count()
            like_dict.append({'id': vid_profile.id, 'count': like_count})
            video_share = Share.objects.filter(skigit_id=vid_profile, is_active=True).count()
            share_dict.append({'id': vid_profile.id, 'count': video_share})
            video_plug = VideoDetail.objects.filter(plugged_skigit=vid_profile.skigit_id, is_plugged=True,
                                                    status=1).count()
            plug_dict.append({'id': vid_profile.id, 'count': video_plug})
            if vid_profile.made_by:
                us_profile = Profile.objects.get(user=vid_profile.made_by)
                us_profile.made_by = vid_profile.made_by.id
                if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                    us_profile.business_logo = us_profile.logo_img.filter(is_deleted=False).all()[0]
                profile_dic.append(us_profile)
        profile_dic = list(set(profile_dic))

        for vid_data in vid:
            sharObj = Share.objects.filter(~Q(to_user=None),skigit_id=vid_data, is_active=True, user=request.user.id).order_by('to_user',
                                                                                                              '-pk').distinct(
                'to_user')
            for sh in sharObj:
                ski_share_list.append(
                    {'share_date': sh.created_date, 'username': sh.to_user.username, 'vid': sh.skigit_id_id})

    except ObjectDoesNotExist:
        messages.error(request, 'No Skigits found...!!!')
        return HttpResponseRedirect("/")
    user = User.objects.get(id=int(user_id))

    like_skigit = []
    if request.user.is_authenticated:
        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        for likes in video_likes:
            like_skigit.append(likes.skigit_id)

    friend_list = []
    if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1).exists():
        f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1)
        from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user', flat=True).distinct()
        to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user', flat=True).distinct()
        fr_list = list(merge(from_user_list, to_user_list))
        friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')
        for friends in friends_detail:
            if friends.profile_img:
                # l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
            else:
                l_img = "{0}{1}".format(settings.STATIC_HOST_URL, 'images/noimage_user.jpg')
            friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                'name': friends.user.get_full_name(), 'image': l_img})

    context = {
        'video_detail': vid,
        'category_current': category_current,
        'user': user,
        'user_profile': us_profile,
        'video_likes': like_skigit,
        'like_count': like_dict,
        'video_type': 'c_o_skigit',
        'default_logo': profile_dic,
        'friend_list': friend_list,
        'video_share': share_dict,
        'video_plug': plug_dict,
        'skigit_list': ski_share_list,
        'users': get_all_logged_in_users()
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


@login_required(login_url='/login')
@csrf_protect
def share_to_friends(request):
    response_data = {}
    if request.is_ajax() and request.method == 'POST':
        # try:
        time_zone = request.POST.get('time_zone', '')
        video_id = request.POST.get('vid_id', None)
        friend_list = request.POST.getlist('friend_list[]', None)
        # notify = Profile.objects.filter(user=request.user).values('share_notify')
        response_data = manage_share_video(request.user.id, time_zone, video_id, friend_list)

    return JsonResponse(response_data)


@login_required(login_url='/login')
def email_share_friends(request):
    response_data = {}
    if request.is_ajax() and request.method == 'POST':
        try:
            data = request.POST
            email_list = data.get('email_list', '')
            video_id = data.get('video_id', None)
            response_data = manage_share_video_to_email(request.user.id, video_id, email_list.split(','))
        except Exception as exc:
            response_data['is_success'] = False
            response_data['message'] = 'Skigit Share failed'
            logger.error("Share skigit to Email is failed: ", exc)
    return JsonResponse(response_data)


@csrf_protect
def i_am_following(request):
    """
        Follow Skigit User
    """
    response_data = {}
    is_success = False
    is_follow, message = None, None
    follow_id = request.POST.get('follow_id', None)
    skigit_id = request.POST.get('skigit_id', None)
    if request.is_ajax() and request.method == 'POST':

        if follow_id and follow_id is not None:
            if request.user.is_authenticated:
                user = request.user
                is_found = User.objects.get(pk=follow_id)
                video_detail = get_object_or_None(VideoDetail, skigit_id__id=skigit_id)
                if is_found:
                    try:
                        video_detail_id = video_detail.id if video_detail else ''
                        result = make_follow(follow_id, user.id, video_detail_id=video_detail_id)
                        message = result['message']
                        is_success = result['is_success']
                        is_follow = result['is_follow']
                    except MultipleObjectsReturned:
                        message = "Oops ! Server Encounter An " \
                                  "Error Into This follow Skigit"
                        is_success = False
                        response_data['message'] = message
                        response_data['is_success'] = is_success
                        response_data['is_follow'] = is_follow
                        return JsonResponse(response_data)
                else:
                    message = "Invalid User Identity"
            else:
                message = "Please Login And Then Try To Follow User"
        else:
            message = "Skigit User Identity Not Found"
    else:
        message = "Invalid Request"
    response_data['message'] = message
    response_data['is_follow'] = is_follow
    response_data['is_success'] = is_success
    return JsonResponse(response_data)


@csrf_protect
def un_following(request):
    """
        Un Follow Skigit User
    """
    response_data = {}
    is_success = False
    is_follow, message = None, None
    follow_id = request.POST.get('follow_id', None)
    if request.is_ajax() and request.method == 'POST':
        user = request.user
        is_found = User.objects.get(pk=follow_id)
        if follow_id and follow_id is not None:
            if request.user.is_authenticated:
                if Follow.objects.filter(user=request.user.id, follow=follow_id, status=True).exists():
                    try:
                        result = make_unfollow(follow_id, user.id)
                        message = result['message']
                        is_success = result['is_success']
                        is_follow = result['is_follow']
                    except MultipleObjectsReturned:
                        message = "Oops ! Server Encounter An " \
                                  "Error Into This Skigit Like"
                        is_success = False
                        response_data['message'] = message
                        response_data['is_success'] = is_success
                        response_data['is_follow'] = is_follow
                        return JsonResponse(response_data)
                else:
                    message = "Invalid follower Identity"
            else:
                message = "Please Login And Then Try To Unfollow Skigit User"
        else:
            message = "Skigit User Identity Not Found"
    else:
        message = "Invalid Request"
    response_data['message'] = message
    response_data['is_follow'] = is_follow
    response_data['is_success'] = is_success
    return JsonResponse(response_data)


@csrf_exempt
def skigit_i_like(request):
    """
     Like skigit
    """
    skigit_id, message, like_count, is_found, like = None, None, None, None, None
    is_success = False
    response_data = {}
    skigit_id = request.POST.get('skigit_id', None)
    if request.is_ajax() and request.method == 'POST':
        if skigit_id and skigit_id is not None:
            if request.user.is_authenticated:
                user = request.user
                video_detail = get_object_or_None(VideoDetail, skigit_id=skigit_id)

                if video_detail:
                    try:
                        result = make_like(video_detail.id, user.id)
                        message = result['message']
                        is_success = result['is_success']
                        like = result['like']

                    except MultipleObjectsReturned:
                        message = "Oops ! Server Encounter An " \
                                  "Error Into This Skigit Like"
                        is_success = False
                        response_data['message'] = message
                        response_data['is_success'] = is_success
                        response_data['like'] = like
                        return JsonResponse(response_data)
                else:
                    message = "Invalid Skigit Identity"
            else:
                message = "Please Login And Then Try To Like Skigit"
        else:
            message = "Skigit Identity Not Found"
    else:
        message = "Invalid Request"
    response_data['message'] = message
    response_data['like'] = like
    response_data['is_success'] = is_success
    return JsonResponse(response_data)


@csrf_exempt
def skigit_i_unlike(request):
    skigit_id, message, like_count, is_found, unlike = None, None, None, None, None
    is_success = False
    response_data = {}
    unlike = 0
    skigit_id = request.POST.get('skigit_id', None)
    if request.is_ajax() and request.method == 'POST':
        user = request.user
        video_detail = get_object_or_None(VideoDetail, skigit_id=skigit_id)
        if video_detail:
            if request.user.is_authenticated:
                user = request.user
                if Like.objects.filter(skigit__id=skigit_id, user_id=user.id).exists():
                    try:
                        result = make_unlike(video_detail.id, user.id)
                        message = result['message']
                        is_success = result['is_success']
                        unlike = result['unlike']

                    except MultipleObjectsReturned:
                        message = "Oops ! Server Encounter An " \
                                  "Error Into This Skigit Like"
                        is_success = False
                        response_data['message'] = message
                        response_data['is_success'] = is_success
                        response_data['unlike'] = unlike
                        return JsonResponse(response_data)
                else:
                    message = "Invalid Skigit Identity"
            else:
                message = "Please Login And Then Try To Like Skigit"
        else:
            message = "Skigit Identity Not Found"
    else:
        message = "Invalid Request"
    response_data['message'] = message
    response_data['unlike'] = unlike
    response_data['is_success'] = is_success
    return JsonResponse(response_data)


@csrf_exempt
def my_favourite_skigit(request):
    """
         Favourite skigit
    """
    response_data = {}
    is_success = False
    is_fav, message = None, None
    skigit_id = request.POST.get('skigit_id', None)
    if request.is_ajax() and request.method == 'POST':
        if skigit_id and skigit_id is not None:
            if request.user.is_authenticated:
                user = request.user
                video_detail = get_object_or_None(VideoDetail, id=skigit_id)

                if video_detail:
                    try:
                        result = make_favourite(video_detail.id, user.id)
                        message = result['message']
                        is_fav = result['is_fav']
                        is_success = result['is_success']
                    except MultipleObjectsReturned:
                        message = "Oops ! Server Encounter An " \
                                  "Error Into This Favorite Skigit"
                        is_success = False
                        response_data['message'] = message
                        response_data['is_success'] = is_success
                        response_data['is_fav'] = is_fav
                        return JsonResponse(response_data)
                else:
                    message = "Invalid Skigit Identity"
            else:
                message = "Please Login And Then Try To Like Skigit"
        else:
            message = "Skigit Identity Not Found"
    else:
        message = "Invalid Request"
    response_data['message'] = message
    response_data['is_fav'] = is_fav
    response_data['is_success'] = is_success
    return JsonResponse(response_data)


@csrf_exempt
def un_favourite_skigit(request):
    """
         Unfavoured skigit
    """
    response_data = {}
    is_success = False
    is_fav, message = None, None
    skigit_id = request.POST.get('skigit_id', None)
    if request.is_ajax() and request.method == 'POST':
        if skigit_id and skigit_id is not None:
            if request.user.is_authenticated:
                user = request.user
                vid = get_object_or_None(VideoDetail, id=skigit_id)
                if Favorite.objects.filter(skigit__id=vid.skigit_id.id, user_id=user.id).exists():
                    try:
                        result = make_unfavourite(vid.id, user.id)
                        message = result['message']
                        is_fav = result['is_fav']
                        is_success = result['is_success']
                    except MultipleObjectsReturned:
                        message = "Oops ! Server Encounter An " \
                                  "Error Into This Skigit Like"
                        is_success = False
                        response_data['message'] = message
                        response_data['is_success'] = is_success
                        response_data['is_fav'] = is_fav
                        return JsonResponse(response_data)
                else:
                    message = "Invalid Skigit Identity"
            else:
                message = "Please Login And Then Try To Like Skigit"
        else:
            message = "Skigit Identity Not Found"
    else:
        message = "Invalid Request"
    response_data['message'] = message
    response_data['is_fav'] = is_fav
    response_data['is_success'] = is_success
    return JsonResponse(response_data)


def linked_in_share(request, pk):
    """
       Skigit Sharing on Linked In View
    """
    skigit = get_object_or_404(VideoDetail, pk=pk)
    u_profile = Profile.objects.get(user=skigit.skigit_id.user)
    # company_logo_url = get_thumbnail(u_profile.profile_img, '100x100', quality=99).url
    company_logo_url = api_request_images(u_profile.profile_img, quality=99, format='PNG')
    video_share_url = None
    if skigit.business_logo and skigit.made_by:
        if skigit.business_logo.is_deleted is False:
            # skigit_b_logo = get_thumbnail(skigit.business_logo.logo, '100x100', quality=99).url
            skigit_b_logo = api_request_images(skigit.business_logo.logo, quality=99, format='PNG')
            video_share_url = create_share_thumbnails(skigit, skigit.skigit_id.thumbnails.all()[0].url(),
                                                      request.build_absolute_uri(skigit_b_logo),
                                                      request.build_absolute_uri(company_logo_url))
        else:
            u_profile = Profile.objects.get(user=skigit.made_by)
            if u_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                blogo = u_profile.logo_img.filter(is_deleted=False).all()[0]
                # skigit_b_logo = get_thumbnail(blogo.logo, '100x100', quality=99).url
                skigit_b_logo = api_request_images(blogo.logo, quality=99, format='PNG')
                video_share_url = create_share_thumbnails(skigit, skigit.skigit_id.thumbnails.all()[0].url(),
                                                          request.build_absolute_uri(skigit_b_logo),
                                                          request.build_absolute_uri(company_logo_url))
    else:
        video_share_url = create_share_thumbnails(skigit, skigit.skigit_id.thumbnails.all()[0].url())
    video_share_url1 = request.build_absolute_uri(video_share_url)
    return render(request, 'pages/linkedin.html', locals())


@receiver(user_signed_up)
def complete_social_signup(sender, **kwargs):
    """
    Receives user_signed_up signal and provides a hook for populating
    additional user data.
    The user_signed_up signal is sent when a user signs up for an account.
    This signal is typically
    followed by a user_logged_in, unless e-mail verification prohibits the user
    to log in.

    You may populate user data collected from social login's extra info, or
    other user data here.
    """
    user = kwargs.pop('user')
    request = kwargs.pop('request')
    profile, created = Profile.objects.get_or_create(user=user)

    if user.socialaccount_set.exists():
        social_account = user.socialaccount_set.all()[0]
        extra_data = social_account.extra_data
        unique_filename = uuid.uuid4()
        profile_img = "skigit/profile/{0}.jpg".format(unique_filename)
        picture_url = ""
        first_name = ''
        last_name = ''
        email = ''

        if ('picture' in extra_data and 'data' in extra_data['picture'] and
                'url' in extra_data['picture']['data']):
            picture_url = extra_data['picture']['data']['url']
        if 'profile_picture' in extra_data:
            picture_url = extra_data['profile_picture']
        if 'profile_image_url' in extra_data:
            picture_url = extra_data['profile_image_url']
        if 'full_name' in extra_data:
            if extra_data['full_name'].find(' ') >= 0:
                first_name, last_name = extra_data['full_name'].rsplit(' ', 1)
            else:
                first_name, last_name = extra_data['full_name'], ''

        if first_name:
            user.first_name = first_name
            user.last_name = last_name
            profile.first_name = first_name
            profile.last_name = last_name
            user.save()
        if picture_url:
            file_path_name = "{0}/media/{1}".format(settings.BASE_DIR.replace('\\', '/'),
                                                    profile_img)
            file_path = handle_uploaded_file_from_url(file_path_name, picture_url)
            profile.profile_img = profile_img
        profile.save()


@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    """
        Email Confirmation View.
    """
    # new_email_address = EmailAddress.objects.get(email=email_address)
    user = User.objects.get(email=email_address.email)
    user.is_active = True
    messages.success(request, 'Your Account Activated SuccessFully')
    user.save()


def handle_uploaded_file_from_url(file_path_name, file_url):
    """
        Updating file Uploading View.
    """
    file = urllib.request.urlopen(file_url)
    with open(file_path_name, 'wb+') as destination:
        destination.write(file.read())
    return file_path_name


def handle_uploaded_file(f, unique_filename):
    """
        Updating file Uploading View.
    """
    file_path = "%s/media/skigit/profile/%s" % ((settings.BASE_DIR).replace('\\', '/'), unique_filename)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path


def handle_uploaded_coupan_img(f, unique_filename):
    """
        Updating Coupan Image View.
    """
    file_path = "%s/media/skigit/coupan/%s" % ((settings.BASE_DIR).replace('\\', '/'), unique_filename)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path


def handle_uploaded_business_logo(f, unique_filename):
    """
        Updating Business Logo View.
    """
    file_path = "%s/media/skigit/logo/%s" % ((settings.BASE_DIR).replace('\\', '/'), unique_filename)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path

def handle_uploaded_business_doc(f, unique_filename):
    """
        Updating Business document.
    """
    file_path = "skigit/doc/%s" % (unique_filename)

    fss = FileSystemStorage(location='media/skigit/doc/')
    fss.save(unique_filename, f)

    return file_path


def handle_uploaded_video(f, unique_filename):
    """
        Video Updating/ Handleing View.
    """
    file_path = "%s/media/videos/%s" % ((settings.BASE_DIR).replace('\\', '/'), unique_filename)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path


@csrf_exempt
@login_required(login_url='/login')
def delete_business_logo(request):
    context = {}
    file_name = request.POST.get('file_name', '')
    user = request.user
    logos = user.profile.logo_img.filter(logo=file_name)
    if logos.exists():
        # on delete logo image, set new logo for all linked skigits
        next_logo = user.profile.logo_img.exclude(logo=file_name).order_by('id').first()
        VideoDetail.objects.filter(business_logo=logos.first()).update(business_logo=next_logo)
        BusinessLogoInvoice.objects.filter(business_logo=logos.first()).update(business_logo=next_logo)
        logos.delete()
    context.update({'is_success': "delete_success", 'message': "skigit/logo/%s" % file_name})

    return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/login')
def delete_extra_profile_image(request):
    context = {}
    file_name = request.POST.get('file_name', '')
    user = request.user
    user.profile.extra_profile_img.filter(profile_img=file_name).delete()

    context.update({'is_success': "delete_success", 'message': "%s" % file_name})

    return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/login')
def profile_extra_image(request):
    user = request.user
    context = upload_extra_profile_image(user, request.FILES, file_field_name='file')

    return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/login')
def business_logo(request):
    user = request.user
    context = upload_business_logo(user, request.FILES, file_field_name='file')
    return JsonResponse(context)

@csrf_exempt
@login_required(login_url='/login')
def business_doc(request):
    user = request.user
    img_url = request.build_absolute_uri('{}images/word.jpg'.format(settings.STATIC_URL))
    context = upload_business_doc(user, img_url, request.FILES, file_field_name='file[0]')

    return JsonResponse(context)

@login_required(login_url='/login')
def business_doc_get_target(request):
    
    user_profile = request.user.profile
    img_url = request.build_absolute_uri('{}images/word.jpg'.format(settings.STATIC_URL))
    context = [{'doc': request.build_absolute_uri(i['doc']),
                'url': img_url} for i in user_profile.business_doc.values("doc")]
    return JsonResponse(context, safe=False)


@csrf_exempt
@login_required(login_url='/login')
def delete_business_doc(request):
    context = {}
    file_name = request.POST.get('file_name', '')
    user = request.user
    doc = user.profile.business_doc.filter(doc=file_name)
    if doc.exists():
        doc.delete()
        context.update({'is_success': "delete_success", 'message': "skigit/doc/%s" % file_name})
    else:
        context.update({'is_success': "delete_failed", 'message': "no record"})
    return JsonResponse(context)

@login_required(login_url='/login')
def business_logo_get_target(request):
    user_profile = request.user.profile
    context = [{'logo': i['logo'],
               'url': request.build_absolute_uri("{0}{1}".format(settings.MEDIA_URL, i['logo']))}
               for i in user_profile.logo_img.filter(is_deleted=False).values("logo")]
    return JsonResponse(context, safe=False)


@csrf_exempt
@login_required(login_url='/login')
def profile_pic(request):
    user = request.user
    context = upload_profile_image(user, request.FILES, file_field_name='p_pic')
    return JsonResponse(context)


@csrf_exempt
@login_required(login_url='/login')
def coupan_image_upload(request):
    user = request.user
    context = upload_coupon_image(user, request.FILES, file_field_name='coupan_img')
    return JsonResponse(context)


@login_required(login_url='/login')
def profile_get_target(request):
    user_profile = request.user.profile
    context = [{'profile_img': i['profile_img'],
                'url': request.build_absolute_uri("{0}{1}".format(settings.MEDIA_URL, i['profile_img']))}
               for i in user_profile.extra_profile_img.values("profile_img")]
    return JsonResponse(context, safe=False)


def get_youtube_video_thumbnail(request):
    video_id = request.POST.get('video_id')
    vdo_obj = Video.objects.get(id=str(video_id))
    thumbnail = Thumbnail.objects.filter(video=vdo_obj)[0]
    thumbnail_url = thumbnail.get_absolute_url()

    return JsonResponse({'url': thumbnail_url, 'is_success': True})


def login_require(request):
    context = {}
    next = request.GET.get('next', '/')
    context.update({'next': next})

    if request.user.is_authenticated:
        logout(request)
        return HttpResponseRedirect(next)
    elif request.method == 'POST' and 'login_submit_required' in request.POST:
        username = request.POST.get('log', None)
        password = request.POST.get('pwd', None)
        user = authenticate(username=username, password=password)
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect(next)
            else:
                # An inactive account was used - no logging in!
                context.update(csrf(request))
                context.update(
                    {'login_error': 'Your Skigit account is disabled.', 'next': next})
                return render(request, 'registration/login_required.html',
                              context)
        else:
            # Bad login details were provided. So we can't log the user in.
            context.update(csrf(request))
            msg = "Invalid login details: {0}, {1}".format(username, password)
            context.update({'login_error': msg, 'next': next})
            return render(request, 'registration/login_required.html',
                          context)
    else:
        context.update(csrf(request))
        return render(request, 'registration/login_required.html', context)


"""
def register_confirm(request, activation_key):
    context = {}

    if request.user.is_authenticated:
        HttpResponseRedirect('/')

    try:
        user_profile = Profile.objects.get(activation_key=activation_key)
    except ObjectDoesNotExist:
        messages.error(request, 'Invalid Account Activation Link.')
        return HttpResponseRedirect('/')
    if user_profile:
        if FriendInvitation.objects.filter(to_user_email=user_profile.user.email).exists():
            invite_obj = FriendInvitation.objects.get(to_user_email=user_profile.user.email)
            friend = Friend()
            friend.to_user = user_profile.user
            friend.from_user = invite_obj.from_user
            friend.status = "1"
            FriendInvitation.objects.filter(to_user_email=user_profile.user.email).update(status='1', is_member=True)
            friend.save()

        user_profile.activation_key = None
        user_profile.save()
        user = user_profile.user
        user.is_active = True
        user.save()
        confirm_path = '/admin/auth/user/%s/' % user.id
        confirm = request.build_absolute_uri(confirm_path)
        subject = "Account Verification Task"
        message = "<table style='width:100%;' cellpadding='0' cellspacing='0'>"\
                         "<tr><td style='text-align:center;'><h3 style='color:#d22b2b;' margin-bottom:0;font-family: "+"Proza Libre"+", sans-serif;'>"\
                         "Account Verification Task - Admin </h3></td></tr>"\
                         "<tr><td><p style='text-align:justify;font-family: "+"Proza Libre"+", sans-serif;'>"\
                         "<span style='color:#1C913F;font-family: "+"Proza Libre"+", sans-serif;'>"+user.username+"</span>has joined skigit. please verify account information by clicking the link below.</p>"\
                         "<p><br/></p></td></tr>"\
                         "<tr><td style='text-align:center;'><a href='"+confirm+"' style='text-decoration:none;color:#0386B8;margin: 20px auto;display: table;font-family: "+"Proza Libre"+", sans-serif;'>"\
                         "User Account Verification </a></td></tr>"\
                         "<tr><td style='text-align:center; width:165px;'><img src='https://static.skigit.com/skigit/images/shair.png' style='width:200px;'/></td></tr>"\
                         "</table>"
        admin_user = User.objects.filter(is_superuser=True).first()

        messages.success(request, 'Account activated successfully. '
                                  'Please login with your credentials')
        return HttpResponseRedirect('/login')
    else:
        messages.error(request, 'Invalid account activation link. '
                                'User account not found')
        return HttpResponseRedirect('/')
"""


def register_type(request):
    context = {}

    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    elif request.method == 'POST':
        if 'register_type' in request.POST:
            form = request.POST.get('acc_type', None)
            if form is not None and form == 'general':
                form = RegistrationForm()
                context.update({'form': form})
                return render(request,
                              'registration/register_as_general_user.html',
                              context
                              )
            elif form is not None and form == 'business':
                form = RegistrationForm()
                context.update({'form': form})
                return render(request,
                              'registration/register_as_business_user.html', context
                              )
            else:
                context.update(csrf(request))
                return render(request,
                              'registration/registration_type.html', context
                              )
        elif 'register_as_general_user' in request.POST:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1'],
                    email=form.cleaned_data['email'],
                )

                user.is_active = False
                user.save()
                g = Group.objects.get(name=str(settings.GENERAL_USER))
                g.user_set.add(user)

                username = form.cleaned_data['username']
                email = form.cleaned_data['email']
                random_string = str(random.random()).encode('utf8')
                salt = hashlib.sha1(random_string).hexdigest()[:5]
                salted = (salt + email).encode('utf8')
                activation_key = hashlib.sha1(salted).hexdigest()
                key_expires = datetime.today() + timedelta(1)

                # Save The Hash to user Profile
                new_profile = Profile(user=user, activation_key=activation_key, key_expires=key_expires)
                new_profile.save()

                email_subject = 'Welcome to Skigit!'
                confirm_path = "/register/confirm/%s" % activation_key
                confirm = request.build_absolute_uri(confirm_path)
                # email_body ="<table style='width:100%;' cellpadding='0' cellspacing='0'>"\
                #             "<tr><td style='text-align:center;'><h3 style='color:#0386B8; margin-bottom:0;font-family: "+"Proza Libre"+", sans-serif;'>"\
                #             "Welcome to Skigit!</h3></td></tr>"\
                #             "<tr><td style='text-align:center;'><h5 style='color:#1C913F; margin-top:10px; font-family: "+"Proza Libre"+", sans-serif;'>"\
                #             "We're so glad you joined us!</h5></td></tr>"\
                #             "<tr><td style='color:#222;'><p style='text-align:justify;'>"\
                #             "Please click the link below so that we can confirm your email address. Without verification, you won't be able to establish an accounts and create Skigits.</p>"\
                #             "<p>Thank you,<br/>Skigit</p></td></tr>"\
                #             "<tr><td style='text-align:center;'><a href='" + confirm + "' style='text-decoration:none;color:#0386B8;margin: 20px auto;display: table;font-weight: 700;font-size: 15px; font-family: "+"Proza Libre"+", sans-serif;'> Click to verify your Email </a></td></tr>"\
                #             "<tr><td style='text-align:center;width:165px;'><img src='https://static.skigit.com/skigit/images/shair.png' style='width:165px;'/></td></tr>"\
                #             "</table>"\

                # header_text = ""
                # send_email(email_subject, email_body, email, header_text, settings.EMAIL_HOST_USER)

                EmailTemplate.send(
                    template_key="new_registration_confirm_general",  # EDIT
                    emails=email,
                    context={"confirm_link": confirm}
                )

                context.update({'user': user})
                return render(request,
                              'registration/register_success.html',
                              context
                              )
            else:
                context.update({'form': form})
                return render(request,
                              'registration/register_as_general_user.html',
                              context
                              )
        elif 'register_as_business_user' in request.POST:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1'],
                    email=form.cleaned_data['email'],
                )
                user.is_active = False
                user.save()
                g = Group.objects.get(name=settings.BUSINESS_USER)
                g.user_set.add(user)

                username = form.cleaned_data['username']
                email = form.cleaned_data['email']
                random_string = str(random.random()).encode('utf8')
                salt = hashlib.sha1(random_string).hexdigest()[:5]
                salted = (salt + email).encode('utf8')
                activation_key = hashlib.sha1(salted).hexdigest()
                key_expires = datetime.datetime.today() + datetime.timedelta(1)

                # Save The Hash to user Profile
                new_profile = Profile(user=user, activation_key=activation_key,
                                      key_expires=key_expires)
                new_profile.save()

                email_subject = 'Welcome to Skigit | Skigit'
                confirm_path = "/register/confirm/%s" % activation_key
                confirm = request.build_absolute_uri(confirm_path)
                # email_body ="<table style='width:100%;' cellpadding='0' cellspacing='0'>"\
                #             "<tr><td style='text-align:center;'><h3 style='color:#0386B8; margin-bottom:0;font-family: "+"Proza Libre"+", sans-serif;'>"\
                #             "Welcome to Skigit!</h3></td></tr>"\
                #             "<tr><td style='text-align:center;'><h5 style='color:#1C913F; margin-top:10px; font-family: "+"Proza Libre"+", sans-serif;'>"\
                #             "We're so glad you joined us!</h5></td></tr>"\
                #             "<tr><td style='color: #222;'><p style='text-align:justify;'>"\
                #             "Please click the link below so that we can confirm your email address. Without verification, you won't be able to establish an accounts and create Skigits.</p>"\
                #             "<p>Thank you,<br/>Skigit</p></td></tr>"\
                #             "<tr><td style='text-align:center;'><a href='" + confirm + "' style='text-decoration:none;color:#0386B8;margin: 20px auto;display: table;font-weight: 700;font-size: 15px; font-family: "+"Proza Libre"+", sans-serif;'> Click to verify your Email </a></td></tr>"\
                #             "<tr><td style='text-align:center;width:165px;'><img src='https://static.skigit.com/skigit/images/shair.png' style='width:165px;'/></td></tr>"\
                #             "</table>"
                # email_body = email_body
                # header_text = ""
                # send_email(email_subject, email_body, email, header_text, settings.EMAIL_HOST_USER)

                EmailTemplate.send(
                    template_key="new_registration_confirm_business",  # EDIT
                    emails=email,
                    context={"confirm_link": confirm}
                )

                context.update({'user': user})

                return render(request,
                              'registration/register_success.html',
                              context
                              )
            else:
                context.update({'form': form})
                return render(request,
                              'registration/register_as_business_user.html',
                              context
                              )
        else:
            context.update(csrf(request))
            return render(request,
                          'registration/registration_type.html',
                          context
                          )

    else:
        context.update(csrf(request))
        return render(request,
                      'registration/registration_type.html',
                      context
                      )


@login_required(login_url='/login')
def user_profile_notifications(request):
    context = {}
    user = request.user
    context['is_business'] = is_user_business(user)
    field = 'user_profile_notification_submit'
    if request.method == 'POST' and field in request.POST:

        form1 = ProfileNotificationForm(request.POST, instance=user.profile)
        if form1.is_valid():
            form1.save()
            messages.success(request, 'Notification settings updated successfully!')
            form1 = ProfileNotificationForm(instance=user.profile)
    else:

        form1 = ProfileNotificationForm(instance=user.profile)
        Profile.objects.get_or_create(user=user)

    user_profile = Profile.objects.get(user=user)
    context.update(csrf(request))
    context['form1'] = form1
    context['user'] = user
    context['user_profile'] = user_profile

    return render(request, 'profile/user_profile_notifications.html', context)


@login_required(login_url='/login')
def my_statistics(request):
    context = {}
    context['is_business'] = is_user_business(request.user)
    user_statistics = get_user_statistics(request.user)
    context.update(user_statistics)
    return render(request, 'profile/my_statistics.html', context)

@method_decorator(login_required(login_url='/login'), name="dispatch")
class BusinessAnalytics(TemplateView):

    def get(self, request, *args, **kwargs):
      context = {}
      context['is_business'] = is_user_business(request.user)
      analytics_data = get_business_analytics(request.user)
      context.update(analytics_data)
      return render(request, 'profile/business_analytics.html',context)


def get_user_statistics(user):
    skigit_count = VideoDetail.objects.filter(
        skigit_id__user=user,
        status=1, is_active=True
    ).count()
    primary_count = VideoDetail.objects.filter(
        skigit_id__user=user,
        status=1,
        is_plugged=False, is_active=True
    ).count()
    plug_in_count = VideoDetail.objects.filter(
        plugged_skigit_id__in=VideoDetail.objects.filter(status=1).values_list('skigit_id_id', flat=True),
        skigit_id__user=user,
        status=1,
        is_plugged=True,
        is_active=True
    ).count()
    plug_in_my_skigit = VideoDetail.objects.filter(
        plugged_skigit_id__in=VideoDetail.objects.filter(status=1).values_list('skigit_id_id', flat=True),
        plugged_skigit__user=user,
        status=1,
        is_plugged=True,
        is_active=True
    ).count()
    like_count = Like.objects.filter(
        skigit_id__user=user,
        skigit_id__in=VideoDetail.objects.filter(status=1).values_list('skigit_id_id', flat=True),
        status=True
    ).count()
    favourited_skigits = Favorite.objects.filter(
        user=user,
        status=1
    ).values('skigit_id')
    favorite_count = VideoDetail.objects.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).filter(
        skigit_id__in=favourited_skigits,
        status=1
    ).count()
    follow_count = Follow.objects.filter(user=user, status=True).count()
    follow_me_count = Follow.objects.filter(follow=user, status=True).count()
    f_count1 = Friend.objects.filter(to_user=user.id, status='1').count()
    f_count2 = Friend.objects.filter(from_user=user.id, status='1').count()
    friend_count = f_count1 + f_count2
    share_count = Share.objects.filter(user=user, is_active=True).count()

    return {'skigit_count': skigit_count,
            'primary_count': primary_count,
            'plug_in_count': plug_in_count,
            'plug_to_my_skigit': plug_in_my_skigit,
            'like_count': like_count,
            'favorite_count': favorite_count,
            'follow_count': follow_count,
            'follow_me_count': follow_me_count,
            'friend_count': friend_count,
            'share_count': share_count}


def all_statistic_count(request):
    context = {}
    skigit_count = VideoDetail.objects.filter(skigit_id__user=request.user,
                                              status=1, is_active=True).count()
    primary_count = VideoDetail.objects.filter(skigit_id__user=request.user, status=1,
                                               is_plugged=False, is_active=True).count()
    plug_in_count = VideoDetail.objects.filter(skigit_id__user=request.user, status=1,
                                               is_plugged=True, is_active=True).count()
    plug_in_my_skigit = VideoDetail.objects.filter(plugged_skigit__user=request.user, status=1,
                                                   is_plugged=True, is_active=True).count()
    like_count = Like.objects.filter(user=request.user, status=True).count()
    favorite_count = Favorite.objects.filter(user=request.user, status=1).count()
    follow_count = Follow.objects.exclude(user=request.user).filter(follow=request.user, status=True).count()
    follow_me_count = Follow.objects.exclude(follow=request.user).filter(user=request.user, status=True).count()
    f_count1 = Friend.objects.filter(to_user=request.user.id, status='1').count()
    f_count2 = Friend.objects.filter(from_user=request.user.id, status='1').count()
    friend_count = f_count1 + f_count2
    share_count = Share.objects.filter(user=request.user, is_active=True).count()

    context.update({'skigit_count': skigit_count,
                    'primary_count': primary_count,
                    'plug_in_count': plug_in_count,
                    'plug_to_my_skigit': plug_in_my_skigit,
                    'like_count': like_count,
                    'favorite_count': favorite_count,
                    'follow_count': follow_count,
                    'follow_me_count': follow_me_count,
                    'friend_count': friend_count,
                    'share_count': share_count,
                    })

    return render(request, 'profile/statistics_menu.html', context)

def get_business_analytics(user):
   
    gender_data = []
    country_data = []
    language_data = []
    share_gender_data = []
    colors =  ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4']

    genders_list = VideoDetail.objects.values('created_by__profile__gender')\
                       .order_by('created_by__profile__gender')\
                       .annotate(count=Count('created_by__profile__gender',filter=Q(made_by=user)))

    country_list = VideoDetail.objects.values('created_by__profile__country')\
                       .order_by('created_by__profile__country')\
                       .annotate(count=Count('created_by__profile__country',filter=Q(made_by=user)))

    language_list = VideoDetail.objects.values('created_by__profile__language')\
                       .order_by('created_by__profile__language')\
                       .annotate(count=Count('created_by__profile__language',filter=Q(made_by=user)))
    
    share_genders_list = Share.objects.values('skigit_id__created_by__profile__gender')\
                       .order_by('skigit_id__created_by__profile__gender')\
                       .annotate(count=Count('skigit_id__created_by__profile__gender',filter=Q(skigit_id__made_by=user)))

    date_list_created = VideoDetail.objects.values('created_by__profile__birthdate')\
                       .order_by('created_by__profile__birthdate')\
                       .annotate(count=Count('created_by__profile__birthdate',filter=Q(made_by=user)))
    
    date_list_share = Share.objects.values('skigit_id__created_by__profile__birthdate')\
                       .order_by('skigit_id__created_by__profile__birthdate')\
                       .annotate(count=Count('skigit_id__created_by__profile__birthdate',filter=Q(skigit_id__made_by=user)))


    display_company_logo = VideoDetail.objects.filter(made_by=user).count()
    socail_share = PostInvoice.objects.filter(logo_user=user).count()
    member_share = Share.objects.filter(~Q(to_user=None),skigit_id__made_by=user).count()
    non_member_share = Share.objects.filter(skigit_id__made_by=user,to_user=None).count()
    
    contains_company_logo = list(VideoDetail.objects.filter(made_by=user).values_list('skigit_id', flat=True))
    like_count = Like.objects.filter(skigit__in=contains_company_logo,status=True).count()
    follow_count = Follow.objects.filter(follow=user).count()
    favorite_count = Favorite.objects.filter(skigit__in=contains_company_logo,status=True).count()
    plugged_count = VideoDetail.objects.filter(made_by=user,is_plugged=True).count()
    click_count = BusinessLogoInvoice.objects.filter(logo_user=user).count()
    learnMore_count = LearnMoreInvoice.objects.filter(learn_ski__made_by=user).count()

    for i,(gl,cl,lng,gl_share) in enumerate(itertools.zip_longest(genders_list, country_list,language_list,share_genders_list)):
      gender_dict = {}
      country_dict = {}
      language_dict = {}
      share_gender_dict = {}

      if gl:
        gender = "Male" if gl['created_by__profile__gender'] == 0 else 'Female'

        gender_dict['name'] = gender
        gender_dict['y'] = gl['count']
        gender_dict['color'] = colors[i]
        gender_data.append(gender_dict)

      if cl:
        country_dict['name'] = cl['created_by__profile__country']
        country_dict['y'] = cl['count']
        country_dict['color'] = colors[i+2]
        country_data.append(country_dict)

      if lng:
        language_dict['name'] = lng['created_by__profile__language']
        language_dict['y'] = lng['count']
        language_dict['color'] = colors[i+3]
        language_data.append(language_dict)
      
      if gl_share:
        gender_share = "Male" if gl_share['skigit_id__created_by__profile__gender'] == 0 else 'Female'

        share_gender_dict['name'] = gender_share
        share_gender_dict['y'] = gl_share['count']
        share_gender_dict['color'] = colors[i]
        share_gender_data.append(share_gender_dict)

    share_data = [{
      'name': 'Member Share',
      'y': member_share,
      'color': '#6AF9C4'
    },{
      'name': 'Non-Member Share',
      'y': non_member_share,
      'color': '#FF9655'
    }]

    age_skigit_created = []
    age_skigit_share = []

    age_bin_created = cal_age_bins(date_list_created)
    age_bin_share = cal_age_bins(date_list_share)

    for key in age_bin_created.keys():
      age_skigit_created.append({
        "name": key,
        "y": age_bin_created[key]
      })

    for key in age_bin_share.keys():
      age_skigit_share.append({
        "name": key,
        "y": age_bin_share[key]
      })


    return {'gender': gender_data,
            'country': country_data,
            'language': language_data,
            "age_created": age_skigit_created,
            "age_shared": age_skigit_share,
            "gender_share": share_gender_data,
            "display_company_logo": display_company_logo,
            "share": share_data,
            "socail_share_count": socail_share,
            "like": like_count,
            "favorite": favorite_count,
            "follow": follow_count,
            "plugged": plugged_count,
            "click": click_count,
            "learnMore": learnMore_count,
    }

def _video_params(request, video_id):
    width = request.GET.get("width", "70%")
    height = request.GET.get("height", "350")
    origin = request.get_host()
    return {"video_id": video_id, "origin": origin, "width": width, "height": height}


@login_required(login_url='/login')
def get_sperk(request):
    if request.is_ajax() and request.method == 'POST':
        incentive_detail = None
        user_id = request.POST.get('user_id', None)

        if not user_id:
            data = {'incentive_detail': incentive_detail, 'all_business_logo': ''}
            return HttpResponse(json.dumps(data), content_type="application/json")

        incentive_detail = None
        default_incentive_msg = 'This maker is not offering any Skigit incentives at this time. Check back later!'
        try:
            usr = User.objects.get(id=int(user_id))
        except:
            # incentive_detail = default_incentive_msg
            incentive_detail = None
        if user_id and Profile.objects.filter(user=usr, incentive=1).exists():
            incentive_detail = Profile.objects.get(user=usr).skigit_incentive
            if not incentive_detail:
                incentive_detail = None
        all_business_logo = []
        # get business logo
        profile = Profile.objects.filter(user=usr)
        for prof in profile:
            if prof.logo_img.filter(is_deleted=False).all():
                all_logo_obj = prof.logo_img.filter(is_deleted=False).all()
                for l_obj in all_logo_obj:
                    tmp = []
                    tmp.append(l_obj.id)
                    tmp.append(l_obj.logo.url)
                    all_business_logo.append(tmp)
                    del tmp
        data = {'incentive_detail': incentive_detail, 'all_business_logo': all_business_logo}

        return HttpResponse(json.dumps(data), content_type="application/json")


def get_logo(request):
    """
        Business Logo
    """
    selected_business_user = request.POST.get('buser', None)
    profile = Profile.objects.get(user=selected_business_user)
    busiless_logo = profile.logo_img.filter(is_deleted=False).first.logo
    return HttpResponse(json.dumps({"incentive_detail": busiless_logo}), content_type="application/json")


@payment_required
@require_filled_profile
def category_view(request):
    return render(request, 'sk_cat/category.html', {
        'category': Category.objects.all(),
    })


@payment_required
@require_filled_profile
def category_detail_view(request, cat_slug, template='category/category_bash.html',
                         page_template='includes/skigit_list.html'):
    video_detail = []
    profile_dic = []
    like_dict = []
    share_dict = []
    plug_dict = []

    category_current = Category.objects.get(cat_slug=cat_slug)
    vid_latest_uploaded = VideoDetail.objects.select_related('skigit_id')\
        .filter(status=1, is_active=True,category=category_current).filter(
                Q(receive_donate_sperk__in=[1,2]) | Q(skigit_id__user__is_active=True)
            )

    if request.method == 'POST' and request.POST.get('sort', '') == '0':

        vid_latest_uploaded = vid_latest_uploaded.order_by('updated_date')

        if vid_latest_uploaded:
            vid_latest_uploaded = vid_latest_uploaded[0]
        videos = VideoDetail.objects.filter(category=category_current, status=1,
                                            is_active=True).order_by('updated_date')
        for vid in videos:
            like_count = Like.objects.filter(skigit=vid.skigit_id, status=True).count()
            like_dict.append({'id': vid.id, 'count': like_count})
            video_share = Share.objects.filter(skigit_id=vid, is_active=True).count()
            share_dict.append({'id': vid.id, 'count': video_share})
            video_plug = VideoDetail.objects.filter(plugged_skigit=vid.skigit_id, is_plugged=True, status=1).count()
            plug_dict.append({'id': vid.id, 'count': video_plug})
            video_detail.append(vid)
            if vid.made_by:
                us_profile = Profile.objects.get(user=vid.made_by)
                if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                    vid.default_business_logo = us_profile.logo_img.filter(is_deleted=False).all()[0]
                    us_profile.business_logo = vid.default_business_logo
                    us_profile.made_by = vid.made_by.id
                    if us_profile not in profile_dic:
                        profile_dic.append(us_profile)

                else:
                    vid.default_business_logo = ''
            else:
                vid.default_business_logo = ''
            video_detail.append(vid)

        ski_share_list = []
        for vid_data in videos:
            sharObj = Share.objects.filter(~Q(to_user=None),skigit_id=vid_data, is_active=True,
                                           user=request.user.id).order_by('to_user', '-pk').distinct('to_user')
            for sh in sharObj:
                ski_share_list.append({'share_date': sh.created_date, 'username': sh.to_user.username,
                                       'vid': sh.skigit_id_id})

        like_skigit = []
        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        for likes in video_likes:
            like_skigit.append(likes.skigit_id)
        context = {
            'page_template': page_template,
            'category_current': category_current,
            'video_detail': video_detail,
            'vid_latest_uploaded': vid_latest_uploaded,
            'video_share': share_dict,
            'video_plug': plug_dict,
            'video_likes': like_skigit,
            'like_count': like_dict,
            'skigit_list': ski_share_list,
            'order': 1,
            'order_title': 1,
            'order_views': 1,
            'order_random': 1,
            'order_likes': 1,
            'page_type': 'categorys',
            'users': get_all_logged_in_users()
        }
        if request.is_ajax():
            template = page_template
        return render(request, template, context)
    else:
        vid_latest_uploaded = vid_latest_uploaded.order_by('-updated_date')
        ski_share_list = []
        if vid_latest_uploaded:
            vid_latest_uploaded = vid_latest_uploaded[0]
        videos = VideoDetail.objects.filter(category=category_current, status=1, is_active=True).order_by(
            '-updated_date')
        for vid in videos:
            like_count = Like.objects.filter(skigit=vid.skigit_id, status=True).count()
            like_dict.append({'id': vid.id, 'count': like_count})
            video_share = Share.objects.filter(skigit_id=vid, is_active=True).count()
            share_dict.append({'id': vid.id, 'count': video_share})
            video_plug = VideoDetail.objects.filter(plugged_skigit=vid.skigit_id, is_plugged=True, status=1).count()
            plug_dict.append({'id': vid.id, 'count': video_plug})
            sharObj = Share.objects.filter(~Q(to_user=None),skigit_id=vid, is_active=True, user=request.user.id).order_by('to_user',
                                                                                                         '-pk').distinct(
                'to_user')
            for sh in sharObj:
                ski_share_list.append(
                    {'share_date': sh.created_date, 'username': sh.to_user.username, 'vid': sh.skigit_id_id})
            if vid.made_by:
                us_profile = Profile.objects.get(user=vid.made_by)
                if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                    vid.default_business_logo = us_profile.logo_img.filter(is_deleted=False).all()[0]
                    us_profile.business_logo = vid.default_business_logo
                    us_profile.made_by = vid.made_by.id
                    if us_profile not in profile_dic:
                        profile_dic.append(us_profile)
                else:
                    vid.default_business_logo = ''
            else:
                vid.default_business_logo = ''
            video_detail.append(vid)
        like_skigit = []
        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        for likes in video_likes:
            like_skigit.append(likes.skigit_id)

    friend_list = []
    if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1).exists():
        f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1)
        from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user', flat=True).distinct()
        to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user', flat=True).distinct()
        fr_list = list(merge(from_user_list, to_user_list))
        friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')
        for friends in friends_detail:
            if friends.profile_img:
                # l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
            else:
                l_img = "{0}{1}".format(settings.STATIC_URL, 'skigit/detube/images/noimage_user.jpg')
            friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                'name': friends.user.get_full_name(), 'image': l_img})

    context = {
        'page_template': page_template,
        'category_current': category_current,
        'video_detail': video_detail,
        'default_logo': profile_dic,
        'vid_latest_uploaded': vid_latest_uploaded,
        'friend_list': friend_list,
        'video_share': share_dict,
        'video_plug': plug_dict,
        'video_likes': like_skigit,
        'like_count': like_dict,
        'skigit_list': ski_share_list,
        'order': 1,
        'order_views': 1,
        'order_title': 1,
        'order_random': 1,
        'order_likes': 1,
        'page_type': 'categorys',
        'users': get_all_logged_in_users()
    }
    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def popup_page(request, video_id):
    """
    Displays a video in an embed player
    """

    context = {}

    try:

        vid = VideoDetail.objects.select_related('skigit_id').get(
            skigit_id__id=video_id
        )
        user = None
        user_profile = None
        is_followed = Follow.objects.filter(
            user_id=request.user.id,
            follow_id=vid.skigit_id.user_id
        )

        inapp_reasons = InappropriateSkigitReason.objects.all()
        context.update({'inapp_reasons': inapp_reasons})
        context.update({'is_followed': is_followed})

        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        like_dict = []
        for likes in video_likes:
            like_dict.append(likes.skigit_id)

        if request.user.is_authenticated:
            user = User.objects.get(pk=request.user.id)
            user_profile = Profile.objects.get(user=user)
            fields = [
                user_profile.profile_img,
                user.username,
                user.first_name,
                user.last_name,
                user.email,
                user_profile.birthdate,
                user_profile.language,
                user_profile.country,
                user_profile.state,
                user_profile.city,
                user_profile.zip_code
            ]
            if not all(fields):
                user_profile = Profile.objects.get(user=user)

        # query below return uploaded latest 7 videos by user whos video
        # opend in popup
        skigits_might_like = VideoDetail.objects.select_related(
            'skigit_id'
        ).filter(
            skigit_id__user=vid.skigit_id.user,
            status=True
        ).exclude(
            skigit_id__id=video_id
        ).order_by('-updated_date')[:5]

        social_redirect_path = '%s%s' % (
            settings.SOCIAL_REDIRECT_URL, video_id
        )
        social_redirect_url = request.build_absolute_uri(social_redirect_path)

        context.update({
            'vid': vid,
            'user': user,
            'user_profile': user_profile,
            'skigits_might_like': skigits_might_like,
            'social_redirect_url': social_redirect_url,
            'video_likes': like_dict,
        })

        return render(request, "youtube/yt_popuppage.html", context)

    except ObjectDoesNotExist:
        messages.error(request, 'Skigit details not found...!!!')
        return HttpResponseRedirect('/')


def skigit_data(request, pk):
    video_likes = []
    all_reasion = []
    video_favorite = []
    video_follow = []
    ski_share_list = []
    
    user = request.user

    if VideoDetail.objects.filter(id=pk):
        skigit = get_object_or_404(VideoDetail, pk=pk)

    else:
        return HttpResponseRedirect("/?id=%s" % pk)
    context = {}

    current_date = datetime.datetime.now().date
    
    embed_skigit = EmbedInvoice.objects.filter(skigit_user__id=skigit.skigit_id.user.id, user__id=request.user.id,
                                               billing_month=current_date, embed_ski=skigit).exists()
    if not user.is_anonymous:
        type = get_user_type(user)
        if type == 'general':
            is_business = False
        elif type == 'business':
            is_business = True
    else:
        is_business = False

    time_zone = request.GET.get('time_zone', '')
    count_i_plugged_into = 0
    related_user_list = get_related_users(request.user.id, skigit.skigit_id.user.id)
    all_sub_cat_skigits = VideoDetail.objects.exclude(id=pk).filter(Q(subject_category=skigit.subject_category) |
                                                                    Q(skigit_id__user__in=related_user_list),
                                                                    status=1, is_active=True).order_by('?')
    if not request.user.is_anonymous:
        count_i_plugged_into = VideoDetail.objects.filter(plugged_skigit__user=request.user, status=1,
                                                          is_plugged=True).count()
    if request.user.is_authenticated:
        video_likes = Like.objects.filter(user_id=request.user.id, status=True).values_list("skigit_id__id", flat=True)
        all_reasion = InappropriateSkigitReason.objects.values('id', 'reason_title')
        video_favorite = Favorite.objects.filter(user_id=request.user.id,
                                                 status=1).values_list("skigit_id__id", flat=True)
        video_follow = Follow.objects.filter(user=request.user.id, status=True).values_list("follow__id", flat=True)

    profile_dic = []
    for vid_profile in all_sub_cat_skigits:
        if vid_profile.made_by:
            us_profile = Profile.objects.get(user=vid_profile.made_by)
            us_profile.made_by = vid_profile.made_by.id
            if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                us_profile.business_logo = us_profile.logo_img.filter(is_deleted=False).all()[0]
                profile_dic.append(us_profile)
    profile_dic = list(set(profile_dic))
    current_view_count = skigit.view_count
    video_share_url = None
    u_profile = Profile.objects.get(user=skigit.skigit_id.user)
    # company_logo_url = get_thumbnail(u_profile.profile_img, '100x100', quality=99).url
    company_logo_url = api_request_images(u_profile.profile_img, quality=99, format='PNG')

    if skigit.business_logo and skigit.made_by:
        if skigit.business_logo.is_deleted is False:
            # skigit_b_logo = get_thumbnail(skigit.business_logo.logo, '100x100', quality=99).url
            skigit_b_logo = api_request_images(skigit.business_logo.logo, quality=99, format='PNG')
            video_share_url = create_share_thumbnails(skigit, skigit.skigit_id.thumbnails.all()[0].url(),
                                                      request.build_absolute_uri(skigit_b_logo),
                                                      request.build_absolute_uri(company_logo_url))
        elif skigit.business_logo.is_deleted is True:
            u_profile = Profile.objects.get(user=skigit.made_by)
            if u_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                blogo = u_profile.logo_img.filter(is_deleted=False).all()[0]
                # skigit_b_logo = get_thumbnail(blogo.logo, '100x100', quality=99).url
                skigit_b_logo = api_request_images(blogo.logo, quality=99, format='PNG')
                video_share_url = create_share_thumbnails(skigit, skigit.skigit_id.thumbnails.all()[0].url(),
                                                          request.build_absolute_uri(skigit_b_logo),
                                                          request.build_absolute_uri(company_logo_url))
    else:
        video_share_url = create_share_thumbnails(skigit, skigit.skigit_id.thumbnails.all()[0].url())

    share_obj = Share.objects.exclude(to_user__in=[request.user.id,None]).filter(skigit_id__id=skigit.id, is_active=True,
                                                                      user=request.user.id
                                                                      ).order_by('to_user', '-pk').distinct('to_user')
    if share_obj:
        for sh in share_obj:
            share_date = datetime.datetime.strptime(str(sh.created_date.date()), '%Y-%m-%d').strftime('%d-%b-%Y')
            ski_share_list.append({'share_date': share_date, 'username': sh.to_user.username, 'vid': sh.skigit_id_id})

    friend_list = []
    if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1).exists():
        f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1)
        from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user', flat=True).distinct()
        to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user', flat=True).distinct()
        fr_list = list(merge(from_user_list, to_user_list))
        friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')
        for friends in friends_detail:
            if friends.profile_img:
                # l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
            else:
                l_img = "{0}{1}".format(settings.STATIC_URL, 'skigit/detube/images/noimage_user.jpg')
            friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                'name': friends.user.get_full_name(), 'image': l_img})
    
    context = {
        "skigit": skigit,
        "video_likes": video_likes,
        "embed_skigit_vid": embed_skigit,
        "all_reasion": all_reasion,
        "all_sub_cat_skigits": all_sub_cat_skigits,
        "video_favorite": video_favorite,
        "video_favorite_count": video_favorite,
        "count_i_plugged_into": count_i_plugged_into,
        "default_logo": profile_dic,
        "video_follow": video_follow,
        "friend_list": friend_list,
        "skigit_list": ski_share_list,
        "is_business": is_business,
        "users": get_all_logged_in_users(),
        "video_share_url": request.build_absolute_uri(video_share_url),
    }

    return render(request, "includes/skigit_popup.html", context)


def social_redirect(request, video_id):
    context = {}
    user, vid, category, user_profile, video_likes, category_current = None, None, None, None, None, None

    vid = VideoDetail.objects.select_related('skigit_id').get(
        skigit_id__id=video_id)

    if request.user.is_authenticated:
        user = User.objects.get(pk=request.user.id)
        user_profile = Profile.objects.get(user=user)
        if user_profile.profile_img == '' or user_profile.profile_img is None or user.username == '' or user.username is None or user.first_name == '' or user.first_name is None or user.last_name == '' or user.last_name is None or user.email == '' or user.email is None or user_profile.birthdate == '' or user_profile.birthdate is None or user_profile.language == '' or user_profile.language is None or user_profile.country == '' or user_profile.country is None or user_profile.state == '' or user_profile.state is None or user_profile.city == '' or user_profile.city is None or user_profile.zip_code == '' or user_profile.zip_code is None:
            user_profile = Profile.objects.get(user=user)

    # query below return uploaded latest 7 videos by
    # user whos video opend in popup
    skigits_might_like = VideoDetail.objects.select_related(
        'skigit_id'
    ).filter(
        skigit_id__user=vid.skigit_id.user, status=1
    ).exclude(
        skigit_id__id=video_id
    ).order_by('-updated_date')[:5]

    context.update({
        'vid': vid,
        'user': user,
        'user_profile': user_profile,
        'skigits_might_like': skigits_might_like,
    })

    return render(request, "social_share/social_share.html", context)


@login_required(login_url='/login')
def display_business_logo(request):
    """
    To retrive logo image and display in skigit upload form
    """
    bus_logo = None
    message = "Logo not found"
    is_success = False
    if request.method == 'POST' and request.is_ajax():
        bus_user_id = request.POST['bus_user_id']
        # Check whether the user exist or not
        is_user = User.objects.get(pk=bus_user_id)

        if is_user:
            bus_logo = Profile.objects.get(user=is_user)
            if bus_logo:
                bus_logo = bus_logo.logo_img.url
                message = "User exist"
                is_success = True
            else:
                message = "Logo not found"
                is_success = False
        else:
            message = "User not exist"
            is_success = False

    response_data = {
        "logo_main": bus_logo,
        "message": message,
        "is_success": is_success,
    }

    return JsonResponse(response_data)


def skigit_view_count(request):
    """
    To update view count of skigit
    """
    response_data = {}
    count = None
    is_success = None
    if request.method == 'POST' and request.is_ajax():
        skigit_id = request.POST['skigit_id']

        try:
            total_count = VideoDetail.objects.get(skigit_id=skigit_id)
            count = total_count.view_count + 1
            total_count.view_count = count
            total_count.save()
            is_success = True
        except ObjectDoesNotExist:
            is_success = False

        response_data['view_count'] = count
        response_data['is_success'] = is_success

        return JsonResponse(response_data)


def get_inapp_reason(request):
    # if request.method == 'GET' and request.is_ajax():
    if request.user.is_authenticated:
        user_id = request.user.id
        all_reasion = InappropriateSkigitReason.objects.values('id', 'reason_title')
        return HttpResponse(json.dumps(all_reasion), content_type="application/json")


#@csrf_exempt
def skigit_inapp_reason(request):
    """
        To save data of inappropriate skigit reason form data
    """
    response_data = {}
    if request.method == 'POST' and request.is_ajax():

        skigit_id = request.POST.get('skigit_id', None)
        reason_id = request.POST.get('skigit_reasons', None)
        user_id = None
        message = None

        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = User.objects.filter(is_superuser=True).first().id

        video, video_detail = get_video_detail_obj({'skigit_id': skigit_id})
        response = manage_flag_video(video_detail.id, user_id, reason_id)
        message = response['message']
        is_success = response['is_success']
        
        response_data['skigit_id'] = skigit_id
        response_data['user_id'] = user_id
        response_data['reason_id'] = reason_id
        response_data['is_success'] = is_success
        response_data['message'] = message
        return JsonResponse(response_data)


def inappropriateskigit_status_save(request):
    inappid = request.GET.get("inappid", None)
    status_id = request.GET.get("status_id", None)
    response_data = {}
    response_data['inappid'] = inappid
    response_data['status_id'] = status_id
    obj = InappropriateSkigit.objects.get(pk=inappid)
    obj.status = status_id
    obj.save()
    return JsonResponse(response_data)


def get_username(request):
    """
        Comment: Function For Get Users Name.
        Args:
            request: Requested user information
    """
    response_data = {}
    is_success = False
    message = None
    users = {}

    if request.method == 'POST' and request.is_ajax():
        keyword = request.POST.get('keyword', None)
        if request.user.is_authenticated:
            try:
                users = list(
                    User.objects.filter(username__startswith=keyword).exclude(
                        pk=request.user.id).values('username'))

                is_success = True
                message = "Matched username"
            except:
                is_success = False
                message = "No match found for your request"

    response_data['is_success'] = is_success
    response_data['message'] = message
    response_data['users'] = users
    return JsonResponse(response_data)


@login_required(login_url='/login')
@payment_required
@require_filled_profile
def user_profile_display(request, username):
    """
        Comment: User profile Display Function
        Args:
            request: requested user
            username: User name of user

        Returns: User profile display
    """
    context = {}
    try:
        request_user = User.objects.get(username=username, is_active=True)
    except ObjectDoesNotExist:
        messages.error(request, 'Sorry, Your Request User Not Found.')
        return HttpResponseRedirect('/')  # HttpResponseRedirect
    busniess_logo = []
    like_dict = []
    friend_list = []
    ski_share_list = []
    company_url = None
    if Profile.objects.filter(user=request_user).exists():
        request_user_profile = Profile.objects.get(user=request_user)
        extra_profile_img = request_user_profile.extra_profile_img.all()
        # extra_profile_img_url = [get_thumbnail(profile_img.profile_img, '300x120', quality=99, format='PNG').url for profile_img in extra_profile_img]
        extra_profile_img_url = api_request_images(profile_img.profile_img, quality=99, format='PNG')

    if request_user.is_superuser or (request_user.is_staff and is_user_general(request_user)) or is_user_general(
            request_user):
        user_template = 'profile/general_user_profile.html'
    elif request_user.groups.all()[0].name == settings.BUSINESS_USER:
        user_template = 'profile/busieness_user_profile.html'
    else:
        messages.error(request,
                       'Sorry, Your Request User Account Group Type Not Found.')
        return HttpResponseRedirect('/')

    if request.user.is_authenticated:
        user = request.user
        if is_user_business(request_user):
            for bb_logo in request_user_profile.logo_img.filter(is_deleted=False).all():
                bb_logo.img_id = bb_logo.id
                # bb_logo.l_img = get_thumbnail(bb_logo.logo, '300x120', quality=99, format='PNG').url
                bb_logo.l_img = api_request_images(bb_logo.logo, quality=99, format='PNG')
                busniess_logo.append(bb_logo)
                company_url = ProfileUrl.objects.filter(user=request_user_profile.user)
            context.update({'company_url': company_url})

        user_profile = Profile.objects.get(user=request_user)

        if Embed.objects.filter(to_user=request_user_profile, is_embed=True).exists():
            embed_skigit_list = Embed.objects.filter(to_user=request_user_profile, is_embed=True).values_list(
                'skigit_id', flat=True)

            if request.user.is_authenticated:
                if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1).exists():
                    f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1)
                    from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user',
                                                                                           flat=True).distinct()
                    to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user', flat=True).distinct()
                    fr_list = list(merge(from_user_list, to_user_list))
                    friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')
                    for friends in friends_detail:
                        if friends.profile_img:
                            # l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                            l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
                        else:
                            l_img = "{0}{1}".format(settings.STATIC_URL, 'skigit/detube/images/noimage_user.jpg')
                        friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                            'name': friends.user.get_full_name(), 'image': l_img})
                video_likes = Like.objects.filter(user_id=request.user.id, status=True)
                for likes in video_likes:
                    like_dict.append(likes.skigit_id)
            vid = VideoDetail.objects.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).filter(skigit_id__id__in=embed_skigit_list)
            serializer = VideoDetailSerializer(vid, many=True)
            for vid_data in vid:
                sharObj = Share.objects.filter(~Q(to_user=None),skigit_id=vid_data, is_active=True, user=request_user_profile).order_by(
                    'to_user', '-pk').distinct('to_user')
                for sh in sharObj:
                    ski_share_list.append(
                        {'share_date': sh.created_date, 'username': sh.to_user.username, 'vid': sh.skigit_id_id})
            context.update({'video_detail': serializer.data,
                            'video_likes': like_dict,
                            'friend_list': friend_list,
                            'order_value': '1',
                            'togal_val': '1',
                            'skigit_list': ski_share_list,
                            'users': get_all_logged_in_users()})
        context.update({'user': user, 'user_profile': user_profile})
        context.update({
            'request_user': request_user,
            'request_user_profile': request_user_profile,
            'extra_profile_img_url': extra_profile_img_url,
            'all_logo_url': busniess_logo,

        })
        return render(request, user_template, context)

    else:
        context.update({
            'request_user': request_user,
            'request_user_profile': request_user_profile,
        })

    return render(request, user_template, context)

@login_required(login_url='/login')
@payment_required
@require_filled_profile
def plugged_in_skigits(request, template='category/skigit_plugged_into.html',
                       page_template='includes/skigit_list.html'):
    user = vid = category = user_profile = video_likes = skigit_plug = None
    plug_skigit_list = []
    try:
        skigit_plug = request.user.username
        vid_record = Video.objects.filter(user=request.user.id).values_list('id', flat=True).order_by('-created_date')
        if VideoDetail.objects.filter(skigit_id__id__in=vid_record, status=True, is_plugged=True).exists():
            plug_id = VideoDetail.objects.filter(skigit_id__id__in=vid_record,
                                                 status=True,
                                                 is_plugged=True,
                                                 ).values_list('skigit_id', flat=True)
            vid = VideoDetail.objects.filter(skigit_id__id__in=plug_id,
                                             status=True,
                                             plugged_skigit__id__gte=1)
            for vid_profile in vid:
                pluged_videos = get_object_or_None(VideoDetail, status=True,
                                                   title=vid_profile.plugged_skigit.title)
                if pluged_videos not in plug_skigit_list and pluged_videos is not None:
                    plug_skigit_list.append(pluged_videos)
    except ObjectDoesNotExist:
        messages.error(request, 'No Skigits found...!!!')
        return HttpResponseRedirect("/")

    like_skigit = []
    if request.user.is_authenticated:
        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        for likes in video_likes:
            like_skigit.append(likes.skigit_id)

    context = {
        'video_detail': plug_skigit_list,
        'skigit_plug': skigit_plug,
        'user': user,
        'user_profile': user_profile,
        'video_likes': like_skigit,
        'video_type': 'plugged',
        'can_delete': True
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def delete_liked_skigit(request):
    skigit_id = request.POST.get('skigit_v_id')
    vdo_obj = Video.objects.get(id=int(skigit_id))
    like_obj = Like.objects.get(skigit=vdo_obj)
    like_obj.status = False

    like_obj.save()
    context = {'is_success': "Ture", 'message': "Skigit unliked successfully"}

    return JsonResponse(context)


@login_required(login_url='/login')
@payment_required
@require_filled_profile
def liked_skigits(request, template='category/skigit_plugged_into.html',
                  page_template='includes/skigit_list.html'):
    user = vid = category = user_profile = video_likes = skigit_like = None
    try:
        skigit_like = request.user.username
        liked_skigits = Like.objects.filter(
            user_id=request.user.id, status=True
        ).values('skigit_id')
        vid = VideoDetail.objects.select_related('skigit_id').filter(
            skigit_id__in=liked_skigits,
            status=1
        ).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by('-updated_date')

    except ObjectDoesNotExist:
        messages.error(request, 'No Skigits found...!!!')
        return HttpResponseRedirect("/")

    like_skigit = []
    if request.user.is_authenticated:
        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        for likes in video_likes:
            like_skigit.append(likes.skigit_id)

    context = {
        'video_detail': vid,
        'skigit_like': skigit_like,
        'user': user,
        'user_profile': user_profile,
        'video_likes': like_skigit,
        'video_type': 'liked',
    }
    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def delete_favorite_skigit(request):
    skigit_id = request.POST.get('skigit_v_id')
    vdo_obj = Video.objects.get(id=int(skigit_id))
    fav_obj = Favorite.objects.filter(skigit=vdo_obj)[0]
    fav_obj.status = 0
    fav_obj.save()
    context = {'is_success': True, 'message': "Skigit unfavorite successfully"}

    return JsonResponse(context)


@login_required(login_url='/login')
@payment_required
@require_filled_profile
def favorite_skigits(request, template='category/skigit_plugged_into.html',
                     page_template='includes/skigit_list.html'):
    user = vid = category = user_profile = video_fav = skigit_fav = None
    try:
        skigit_fav = request.user.username
        fav_skigits = Favorite.objects.filter(
            user_id=request.user.id, status=True
        ).values('skigit_id')
        vid = VideoDetail.objects.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).filter(
            skigit_id__in=fav_skigits,
            status=1
        ).order_by('-updated_date')
    except ObjectDoesNotExist:
        messages.error(request, 'No Skigits found...!!!')
        return HttpResponseRedirect("/")

    like_skigit = []
    if request.user.is_authenticated:
        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        for likes in video_likes:
            like_skigit.append(likes.skigit_id)
    context = {
        'video_detail': vid,
        'skigit_fav': skigit_fav,
        'user': user,
        'user_profile': user_profile,
        'video_likes': like_skigit,
        'video_type': 'fav',
        'can_delete': True
    }
    if request.is_ajax():
        template = page_template
    return render(request, template, context)


@login_required(login_url='/login')
def delete_skigit(request):
    response_data = {'is_success': False, 'message': 'Error in delete ajax call'}
    if request.is_ajax() and request.method == 'POST':
        response_data = mark_video_as_deleted(user_id=request.user.id, video_id=request.POST.get('skigit_v_id'))
    return JsonResponse(response_data)


@login_required(login_url='/login')
def unplug_skigit(request):
    response_data = {}
    if request.is_ajax() and request.method == 'POST':
        video_id = request.POST.get('skigit_unplug_id')
        response_data = unplug_video(request.user.id, video_id)
    return JsonResponse(response_data)


@csrf_protect
def email_exits_check(request):
    response_data = {}
    if request.is_ajax() and request.method == 'POST':
        email_id = request.POST.get('email', None)
        is_success, message = check_email_exists(email_id)
    else:
        is_success = False
        message = 'Invalid Request'

    response_data['is_success'] = is_success
    response_data['message'] = message
    return JsonResponse(response_data)

@csrf_protect
def check_social_user(request):
      response_data = {
        "user_exist": False
      }
      provider_data = {
        "linkedin_oauth2": {
          "provider": "linkedIn",
          "login_url": "https://www.linkedin.com/login"
        },
         "facebook": {
          "provider": "facebook",
          "login_url": "https://www.facebook.com/login"
        },
         "twitter": {
          "provider": "twitter",
          "login_url": "https://www.twitter.com/login"
        },
         "instagram": {
          "provider": "instagram",
          "login_url": "https://www.instagram.com/"
        }
      }

      try:
        if request.is_ajax() and request.method == 'POST':
          email_id = request.POST.get('email', None)
          user = User.objects.get(email__iexact=email_id)
          if user.socialaccount_set.all().exists():
            user_aouth = user.socialaccount_set.get(user=user)
            response_data["user_exist"] = True
            response_data["provider"] = user_aouth.provider

            provider_dict = provider_data.get(user_aouth.provider,"facebook")
            response_data.update(provider_dict)
              
          else:
              response_data
        return JsonResponse(response_data)
      except Exception as e:
        return response_data

@login_required(login_url='/login')
@payment_required
@require_filled_profile
def sperks(request, template='sperk/sperk.html', page_template='sperk/sperk_body.html'):
    """
        Comment: Sperk list display by business user who provide incentive
        Args: request: Request method
        Returns: Sperk (First Business Logo)
    """
    if User.objects.filter(id=request.user.id).exists():
        sperk_logo_list = []
        sperk_logo = Profile.objects.filter(incentive=True, business_verified=True).order_by('company_title')
        for b_logo in sperk_logo:
            if b_logo.logo_img.filter(is_deleted=False).all():
                b_logo.img_id = b_logo.logo_img.filter(is_deleted=False).all()[0]
                # b_logo.b_img = get_thumbnail(b_logo.logo_img.filter(is_deleted=False).all()[0].logo, '90x60',
                #                             quality=99, format='PNG').url
                b_logo.b_img = api_request_images(b_logo.logo_img.filter(is_deleted=False).all()[0].logo,
                                                  quality=99,
                                                  format='PNG')
                sperk_logo_list.append(b_logo)

        context = {
            'page_template': page_template,
            'sperk_logo_list': sperk_logo_list,
        }
        if request.is_ajax():
            template = page_template
        return render(request, template, context)


@login_required(login_url='/login')
def sperk_profile(request, user, logo, template='sperk/sperk-profile.html', page_template='includes/skigit_list.html'):
    """
        On Click of Sperk logo page will be redirect to
        Sperk profile, page having information related
        Sperk

    Args:
        request: Requested Method GET POST
        user: user_id
        logo: sperk (Logo id)

    Returns:
        Sperk (Business Logo) detail view

    """
    qr_code = request.GET.get('code') # redirect throught QR code
    if qr_code:
      qr_code_fees(user) # update qr code invoice as it rediirect through QR code

    if User.objects.filter(id=request.user.id).exists():
        ski_share_list = []
        busniess_logo = []
        friend_list = []
        like_dict = []
        id = user
        logoid = logo
        profile_list = Profile.objects.filter(user__id=user)
        try:
            request_user_profile = profile_list[0]
            request_user = User.objects.get(pk=request_user_profile.user.id, is_active=True)
        except ObjectDoesNotExist:
            messages.error(request, 'Sorry, Your Request User Not Found.')
            return HttpResponseRedirect('/')  # HttpResponseRedirect

        if not request_user_profile.is_completed['status']:
            messages.error(request, 'Sorry, Your request user profile is not active.')
            return HttpResponseRedirect('/')

        verified_business = is_verified_business_user(request_user)
        busniesslogo = BusinessLogo.objects.get(id=logo, is_deleted=False)

        for bb_logo in request_user_profile.logo_img.filter(is_deleted=False).all():
            bb_logo.img_id = bb_logo.id
            bb_logo.l_img = get_thumbnail(bb_logo.logo, '{}x{}'.format(bb_logo.logo.width, bb_logo.logo.height),
                                          quality=100, format='PNG').url
            busniess_logo.append(bb_logo)

        company_url = ProfileUrl.objects.filter(user__id=user)

        if Embed.objects.filter(to_user__id=user, is_embed=True).exists():
            embed_skigit_list = Embed.objects.filter(to_user__id=user, is_embed=True).values_list('skigit_id',
                                                                                                  flat=True)
            like_dict = video_likes = Like.objects.filter(user_id=request.user.id, status=True).values_list('skigit__id',
                                                                                                            flat=True)

            vid = VideoDetail.objects.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).filter(skigit_id__id__in=embed_skigit_list)
            request_user = request_user
            # video_detail = serializer.data
            video_detail = vid
            video_likes = like_dict
            order_value = '1'
            togal_val = '1'
            unembed = True if int(user) == int(request.user.id) else False
    if request.is_ajax():
        template = page_template
    return render(request, template, locals())


@csrf_exempt
def bug_management(request):
    response_data = {'is_success': False}
    if request.method == 'POST':
        data = request.POST
        bug_mgm = BugReport()
        bug_mgm.user = request.user
        skigit_id = data.get('skigit_id', '')
        if skigit_id:
            video_inst = VideoDetail.objects.get(id=skigit_id)
            bug_mgm.skigit_id = video_inst

        bug_mgm.bug_page_url = data['bug_url'] if data.get('bug_url', '') else data.get(
            'id_bug_page_url', '')
        bug_mgm.bug_description = data.get('bug_description', '')
        bug_mgm.bug_repeated = False if data.get('bug_repeated', '') in ['0', 0] else True
        bug_mgm.save()
        BugReport.objects.filter(id=bug_mgm.id).update(bug_title='Bug#{}'.format(bug_mgm.id))
        response_data.update(is_success=True,
                             message='&#10004 Bug Report Submitted.')
        return JsonResponse(response_data)


def getSwfURL(video_id):
    url = 'https://www.youtube.com/embed/%s' \
          '?modestbranding=1&showinfo=0&autoplay=0&autohide=1&rel=0&wmode=transparent' % (video_id)
    return url


def getYoutubeURL(video_id):
    url = 'https://www.youtube.com/watch?v=%s' % video_id
    return url


@csrf_exempt
@login_required(login_url='/login')
@payment_required
@require_filled_profile
def copyright(request, ski_id):
    instance = VideoDetail.objects.get(pk=ski_id)
    form = CopyrightInfringementForm(initial={'skigit_id': ski_id})
    skigitt_id = ski_id
    if request.method == 'POST':
        form = CopyrightInfringementForm(request.POST)
        if form.is_valid():
            copy_right = form.save(commit=False)
            user_profile = Profile.objects.get(user__id=request.user.id)
            copy_right.user_id = user_profile.user
            copy_right.submitted_by = user_profile
            copy_right.skigit_id = ski_id
            copy_right.save()

            # set the skigit under open copyright infringement
            instance.copyright_skigit = 0
            instance.save()

            messages.success(request, 'A Copyright Infringement claim has been submitted!')
            form = CopyrightInfringementForm()
            return HttpResponseRedirect('/')
    return render(request, "copyright/copyrightinfregment.html", locals())


@csrf_exempt
def skigit_statistics(request):
    response_data = {'is_success': False}
    like_count = plug_count = fav_count = view_count = share_count = 0
    if request.is_ajax() and request.method == 'POST':
        video_detail_id = request.POST.get("skigit_id", "")
        video_detail = VideoDetail.objects.get(id=video_detail_id)
        try:
            like_count = Like.objects.filter(skigit_id=video_detail.skigit_id.id, status=True).count()
        except:
            like_count = 0
        try:
            fav_count = Favorite.objects.filter(skigit__id=video_detail.skigit_id.id, status=1, is_active=True).count()
        except:
            fav_count = 0
        try:
            plug_count = VideoDetail.objects.filter(plugged_skigit__id=video_detail.skigit_id.id, is_plugged=True, status=1).count()
        except:
            plug_count = 0
        try:
            if VideoDetail.objects.filter(id=video_detail_id, status=1).exists():
                vid = VideoDetail.objects.get(id=video_detail_id, status=1)
                view_count = vid.view_count
            else:
                view_count = 0
        except:
            view_count = 0
        try:
            if Share.objects.filter(skigit_id=video_detail_id, is_active=True).exists():
                share_count = Share.objects.filter(skigit_id=video_detail_id, is_active=True).count()
            else:
                share_count = 0
        except:
            share_count = 0

        response_data['like_count'] = like_count
        response_data['fav_count'] = fav_count
        response_data['plug_count'] = plug_count
        response_data['view_count'] = view_count
        response_data['share_count'] = share_count
        response_data['is_success'] = True
        response_data['message'] = 'Statistic Count.'
    return JsonResponse(response_data)


@login_required(login_url='/login')
@payment_required
@require_filled_profile
def i_am_following_view(request, template='category/skigit_plugged_into.html',
                        page_template='category/i_am_following_body.html'):
    follow_list = []
    try:
        follow_record = Follow.objects.filter(user=request.user.id, status=True).order_by('-follow__first_name')
        for following in follow_record:
            if User.objects.exclude(id=request.user.id).filter(id=following.follow.id).exists():
                user_follow_detail = User.objects.exclude(id=request.user.id).filter(id=following.follow.id)
                for user_detail in user_follow_detail:
                    user_profile = Profile.objects.get(user=user_detail)
                    name = user_detail.get_full_name()
                    if user_profile.profile_img:
                        # l_img = get_thumbnail(user_profile.profile_img, '100x100', quality=99, format='PNG').url
                        l_img = api_request_images(user_profile.profile_img, quality=99, format='PNG')
                    else:
                        l_img = "{0}{1}".format(settings.STATIC_URL, 'skigit/detube/images/noimage_user.jpg')
                    follow_count = Follow.objects.exclude(follow=request.user.id).filter(follow=user_detail.id,
                                                                                         status=True).count()
                    follow_list.append({'user': request.user.id, 'follower': user_detail.id, 'name': name,
                                        'follower_img': l_img, 'username': user_detail.username, 'count': follow_count})
        follow_list = sorted(follow_list, key=lambda follow: (follow['name']))

    except ObjectDoesNotExist:
        messages.error(request, 'No Following user were found...!!!')
        return HttpResponseRedirect("/")

    context = {
        'video_detail': follow_list,
        'current_user': request.user.username,
        'video_type': 'i_am_following',
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


@payment_required
@require_filled_profile
def skigit_search_view(request, template='search/skigit_search.html',
                       page_template="includes/skigit_list.html", videoId=None):
    if request.method == 'GET':

        like_dict = []
        if request.user.is_authenticated:

            video_likes = Like.objects.filter(user_id=request.user.id, status=True)
            for likes in video_likes:
                like_dict.append(likes.skigit_id)

        if videoId is not None:
            vid = VideoDetail.objects.select_related('skigit_id').filter(
                plugged_skigit_id=videoId,
                status=1,
                is_plugged=True,
                is_active=True
            ).filter(
                Q(receive_donate_sperk__in=[1,2]) | Q(skigit_id__user__is_active=True)
            ).order_by('-updated_date')
            template = 'skigit/plugins.html'
        else:
            vid = VideoDetail.objects.select_related('skigit_id').filter(status=1, is_active=True).filter(
                Q(receive_donate_sperk__in=[1,2]) | Q(skigit_id__user__is_active=True)
            ).order_by(
                '-updated_date')

        context = {
            'video_detail': vid,
            'video_likes': like_dict,
            'order_value': '1',
            'togal_val': '1',
        }
        if request.is_ajax():
            template = page_template
        return render(request, template, context)

    if request.method == 'POST':
        togal_val = None
        like_dict = []
        if request.user.is_authenticated:
            video_likes = Like.objects.filter(user_id=request.user.id, status=True)
            for likes in video_likes:
                like_dict.append(likes.skigit_id)
        search_text = request.POST.get('searchBox', None)
        if search_text:
            profile = Profile.objects.filter(Q(company_title__icontains=search_text))
            if profile:
                for p in profile:
                    vid = VideoDetail.objects.select_related(
                        'skigit_id').filter(Q(skigit_id__user__id=p.id) |
                                            Q(skigit_id__user__username__icontains=search_text) |
                                            Q(title__icontains=search_text), status=1, is_active=True
                                            ).order_by('-updated_date')
            else:
                vid = VideoDetail.objects.select_related(
                    'skigit_id').filter(Q(title__icontains=search_text) |
                                        Q(skigit_id__user__username__icontains=search_text),
                                        status=1, is_active=True).order_by('-updated_date')

            context = {
                'video_detail': vid,
                'video_likes': like_dict,
                'search_text': search_text,
                'order_value': '1',
                'togal_val': '1',
            }
            if request.is_ajax():
                template = page_template
            return render(request, template, context)
        else:

            vid = VideoDetail.objects.select_related('skigit_id').filter(status=1, is_active=True).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by(
                '-updated_date')
            context = {
                'video_detail': vid,
                'video_likes': like_dict,
                'search_text': search_text,
                'order_value': '1',
                'togal_val': '1',
            }
            if request.is_ajax():
                template = page_template
            return render(request, template, context)


def search_ordering_skigit(request, order=None,
                           template='search/skigit_search.html',
                           page_template='includes/skigit_list.html'):
    search_text = None
    like_dict = []
    if request.user.is_authenticated:
        video_likes = Like.objects.filter(user_id=request.user.id, status=True)
        for likes in video_likes:
            like_dict.append(likes.skigit_id)

    order = order.split('&')
    if len(order) == 2 and (order[0]).strip() == '1':
        ordering = '-created_date'
        order_by = '2-%s' % order[1]
        togal_val = '2'
        search_text = (order[1]).strip()
    elif len(order) == 2 and (order[0]).strip() == '2':
        ordering = 'created_date'
        order_by = '1-%s' % (order[1]).strip()
        search_text = (order[1]).strip()
        togal_val = '1'
    elif (order[0]).strip() == '2':
        ordering = 'created_date'
        order_by = '1'
        togal_val = '1'
    elif (order[0]).strip() == '1':
        ordering = '-created_date'
        order_by = '2'
        togal_val = '2'

    if search_text:
        profile = Profile.objects.filter(Q(company_title__icontains=search_text))
        if profile:
            for p in profile:
                vid = VideoDetail.objects.select_related(
                    'skigit_id').filter(Q(skigit_id__user__id=p.id) |
                                        Q(skigit_id__user__username__icontains=search_text) |
                                        Q(title__icontains=search_text), status=1, is_active=True
                                        ).order_by(ordering)
                serializer = VideoDetailSerializer(vid, many=True)
        else:
            vid = VideoDetail.objects.select_related(
                'skigit_id').filter(Q(title__icontains=search_text) |
                                    Q(skigit_id__user__username__icontains=search_text),
                                    status=1, is_active=True).order_by(ordering)
            serializer = VideoDetailSerializer(vid, many=True)
        context = {
            'video_detail': vid,
            'video_likes': like_dict,
            'search_text': search_text,
            'order_value': order_by,
            'togal_val': togal_val,
        }
        if request.is_ajax():
            template = page_template
        return render(request, template, context)
    else:
        vid = VideoDetail.objects.select_related('skigit_id').filter(status=1, is_active=True).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by(ordering)
        serializer = VideoDetailSerializer(vid, many=True)
        context = {
            'video_detail': vid,
            'video_likes': like_dict,
            'search_text': search_text,
            'order_value': order_by,
            'togal_val': togal_val,
        }
        if request.is_ajax():
            template = page_template
        return render(request, template, context)


def skigit_count_update(request):
    response_data = {}
    if request.is_ajax() and request.method == 'POST':
        try:
            video_id = request.POST.get('skigit_id', None)
            if VideoDetail.objects.filter(id=int(video_id)).exists():
                vid = VideoDetail.objects.get(id=int(video_id))
                vid.view_count = vid.view_count + 1
                vid.save()
                response_data['view_count'] = vid.view_count
                response_data['is_success'] = True
                response_data['message'] = 'view count updated'
        except ObjectDoesNotExist:
            response_data['is_success'] = False
    return JsonResponse(response_data)


@xframe_options_exempt
def embed_skigit(request, video):
    video_detail = VideoDetail.objects.filter(skigit_id__video_id=video, is_active=True, status=1)
    
    if video_detail.exists():
        skigit = video_detail[0]
        if skigit.business_logo:
          logo_id = skigit.business_logo.id
          logo = BusinessLogo.objects.get(id=logo_id)
          logo_url = str(settings.MEDIA_HOST_URL) + str(logo.logo)
        video_id = video
    else:
        video_id = None
        logo_url = None

    image_url = request.GET.get('href', None)
    return render(request, 'includes/skigit_embed.html', locals())


def sort_by_date(request, cat_slug, order_by, template='category/category_bash.html',
                 page_template='includes/skigit_list.html'):
    like_skigit = []

    category_current = Category.objects.get(cat_slug=cat_slug)

    videos = VideoDetail.objects.filter(category=category_current, status=1, is_active=True).filter(
        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
    )
    if order_by == '1':
        order_by = 2
        videos = videos.order_by('-created_date')
    else:
        order_by = 1
        videos = videos.order_by('created_date')

    video_likes = Like.objects.filter(user_id=request.user.id, status=True)
    for likes in video_likes:
        like_skigit.append(likes.skigit_id)

    context = {
        'page_template': page_template,
        'category_current': category_current,
        'video_detail': videos,
        'video_likes': like_skigit,
        'order': order_by,
        'order_title': 1,
        'order_views': 1,
        'order_random': 1,
        'order_likes': 1,
        'page_type': 'sort_date',
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def sort_by_title(request, cat_slug, order_by, template='category/category_bash.html',
                  page_template='includes/skigit_list.html'):
    like_skigit = []

    category_current = Category.objects.get(cat_slug=cat_slug)

    videos = VideoDetail.objects.filter(category=category_current, status=1, is_active=True).filter(
        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
    )
    if order_by == '1':
        order_by = 2
        videos = videos.order_by('-title')
    else:
        order_by = 1
        videos = videos.order_by('title')

    video_likes = Like.objects.filter(user_id=request.user.id, status=True)
    for likes in video_likes:
        like_skigit.append(likes.skigit_id)

    context = {
        'page_template': page_template,
        'category_current': category_current,
        'video_detail': videos,
        'video_likes': like_skigit,
        'order': 1,
        'order_title': order_by,
        'order_views': 1,
        'order_random': 1,
        'order_likes': 1,
        'page_type': 'sort_title',
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def sort_by_views(request, cat_slug, order_by, template='category/category_bash.html',
                  page_template='includes/skigit_list.html'):
    like_skigit = []

    category_current = Category.objects.get(cat_slug=cat_slug)

    videos = VideoDetail.objects.filter(category=category_current, status=1, is_active=True).filter(
        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
    )
    if order_by == '1':
        order_by = 2
        videos = videos.order_by('-view_count')
    else:
        order_by = 1
        videos = videos.order_by('view_count')

    video_likes = Like.objects.filter(user_id=request.user.id, status=True)
    for likes in video_likes:
        like_skigit.append(likes.skigit_id)

    context = {
        'page_template': page_template,
        'category_current': category_current,
        'video_detail': videos,
        'video_share': videos,
        'video_likes': like_skigit,
        'order': 1,
        'order_title': 1,
        'order_likes': 1,
        'order_random': 1,
        'order_views': order_by,
        'page_type': 'sort_views',
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def sort_by_likes(request, cat_slug, order_by, template='category/category_bash.html',
                  page_template='includes/skigit_list.html'):
    like_skigit = []

    category_current = Category.objects.get(cat_slug=cat_slug)
    videos = VideoDetail.objects.filter(category=category_current, status=1, is_active=True).filter(
        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
    )
    videos = list(videos) if videos.exists() else videos

    video_likes = Like.objects.filter(user_id=request.user.id, status=True)
    for likes in video_likes:
        like_skigit.append(likes.skigit_id)

    videoIds = [vid.skigit_id.id for vid in videos]
    likes = Like.objects.filter(skigit_id__in=videoIds, status=True).values('skigit_id').annotate(
        like_count=Count('skigit_id'))

    likes = {l['skigit_id']: l['like_count'] for l in likes}
    video_detail = []
    for vid in videos:
        vid.like_count = likes[vid.skigit_id.id] if vid.skigit_id.id in likes else 0
        video_detail.append(vid)
    videos = video_detail

    if order_by == '1':
        order_by = 2
        videos.sort(key=operator.attrgetter('like_count'), reverse=True)
    else:
        order_by = 1
        videos.sort(key=operator.attrgetter('like_count'), reverse=False)
    context = {
        'page_template': page_template,
        'category_current': category_current,
        'video_detail': videos,
        'video_likes': like_skigit,
        'order': 1,
        'order_title': 1,
        'order_views': 1,
        'order_random': 1,
        'order_likes': order_by,
        'page_type': 'sort_likes',
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def sort_by_random(request, cat_slug, template='category/category_bash.html',
                   page_template='includes/skigit_list.html'):
    like_skigit = []

    category_current = Category.objects.get(cat_slug=cat_slug)
    videos = VideoDetail.objects.filter(category=category_current, status=1, is_active=True).filter(
        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
    ).order_by('?')

    video_likes = Like.objects.filter(user_id=request.user.id, status=True)
    for likes in video_likes:
        like_skigit.append(likes.skigit_id)

    context = {
        'page_template': page_template,
        'category_current': category_current,
        'video_detail': videos,
        'video_likes': like_skigit,
        'order': 1,
        'order_title': 1,
        'order_views': 1,
        'order_likes': 1,
        'page_type': 'sort_random',
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context)


def ajax_remove_images(request):
    response_data = {'status_code': 404, 'is_success': False, 'message': 'Error into Remove Profile/Coupan Image..'}
    if request.is_ajax() and request.method == 'POST':
        try:
            img = request.POST.get('image_type', None)
            if img == 'profile':
                profile = Profile.objects.get(user=request.user)
                profile.profile_img.delete()
                profile.save()
                response_data['is_success'] = True
                response_data['image_type'] = 'profile'
                response_data['message'] = 'Profile image removed successfully!'
                response_data['status_code'] = 200
            elif img == 'coupan':
                profile = Profile.objects.get(user=request.user)
                profile.coupan_image.delete()
                profile.save()
                response_data['is_success'] = True
                response_data['status_code'] = 200
                response_data['image_type'] = 'coupan'
                response_data['message'] = 'Coupan removed successfully! '
            else:
                response_data['is_success'] = False
                response_data['message'] = 'Image type was profile or coupan.'
                response_data['status_code'] = 200
        except Exception:
            response_data['is_success'] = False
            response_data['message'] = 'Image type was profile or coupan.'
            response_data['status_code'] = 200
    return JsonResponse(response_data)


def check_email_exists(email_id):
    if email_id and email_id != '' and email_id is not None:
        email_check = User.objects.filter(email__iexact=email_id).exists()
        if email_check and email_check is not None:
            is_success = True
            message = ''
        else:
            is_success = False
            message = 'This email address is not found.'
    else:
        is_success = False
        message = 'Please enter a valid email address.'
    return (is_success, message)


class LikedSkigitAPIView(generics.ListAPIView):
    permission_classes = (CustomIsAuthenticated,)
    queryset = VideoDetail.objects.all()
    serializer_class = VideoDetailSerializer
    pagination_class = PageNumberPagination

    def get(self, request, pk):
        result = {'status': '',
                  'message': ''}
        pk = request.user.id if request.auth else 0
        liked_skigits = Like.objects.filter(
            user_id=pk, status=True
        ).values('skigit_id')
        vid = VideoDetail.objects.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).filter(
            skigit_id__in=liked_skigits,
            status=1
        ).order_by('-updated_date')
        page = self.paginate_queryset(vid)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_result = self.get_paginated_response(serializer.data)
            result.update(status='success',
                          message='',
                          data=paginated_result.data)
            return Response(result)

        serializer = self.get_serializer(vid, many=True)
        data = serializer.data
        result.update(status='success',
                      message='',
                      data=data)
        return Response(result)


class FavouriteSkigitAPIView(generics.ListAPIView):
    permission_classes = (CustomIsAuthenticated,)
    queryset = VideoDetail.objects.all()
    serializer_class = VideoDetailSerializer
    pagination_class = PageNumberPagination

    def get(self, request, pk):
        result = {'status': '',
                  'message': ''}
        pk = request.user.id if request.auth else 0
        fav_skigits = Favorite.objects.filter(
            user_id=pk, status=True
        ).values('skigit_id')
        vid = VideoDetail.objects.select_related('skigit_id').filter(
            skigit_id__in=fav_skigits,
            status=1
        ).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by('-updated_date')
        page = self.paginate_queryset(vid)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_result = self.get_paginated_response(serializer.data)
            result.update(status='success',
                          message='',
                          data=paginated_result.data)
            return Response(result)

        serializer = self.get_serializer(vid, many=True)
        result.update(status='success',
                      message='',
                      data=serializer.data)
        return Response(result)


class BugReportViewSet(viewsets.ViewSet):
    serializer_class = BugReportSerializer
    permission_classes = (CustomIsAuthenticated,)

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        data.update(user_id=request.user.id if request.auth else 0)
        user = get_object_or_None(User, id=data['user_id'])
        serializer = self.serializer_class(data=data)
        success_message = "Thanks for making Skigit better!"
        no_user_message = 'User is not found'

        try:
            if serializer.is_valid():
                if user:
                    report = serializer.save(user=user)
                    result.update(status='success',
                                  message=success_message,
                                  data={})
                else:
                    result.update(status='error',
                                  message=no_user_message)
            else:
                result.update(get_error_result(serializer.errors))
        except Exception as exc:
            logger.error("Serializer: BugReportView:", exc)
        return Response(result)


class HelpfulStuffAPIView(views.APIView):
    # serializer_class = VideoDetailSerializer

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        try:
            result.update(status='success',
                          message='',
                          data={
                              'guidelines': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                            reverse('guidelines_api_url:guidelines_view_api')),
                              'skigitology': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                             reverse('guidelines_api_url:skigitology_view_api')),
                              'making_your_skigit': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                    reverse(
                                                                        'guidelines_api_url:making_your_skigit_view_api')),
                              'allowed_video_formats': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                       reverse(
                                                                           'guidelines_api_url:allowed_video_formats_view_api')),
                              'about_us': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                          reverse('aboutus_api_url:about_us_view_api')),
                              'faq': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                     reverse('aboutus_api_url:faq_view_api')),
                              'privacy_policy': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                reverse('aboutus_api_url:privacy_policy_view_api')),
                              'terms_of_service': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                  reverse('aboutus_api_url:t_and_c_view_api')),
                              'acceptable_use_policy': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                       reverse(
                                                                           'aboutus_api_url:acceptable_use_policy_view_api')),
                              'copyright_policy': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                  reverse('aboutus_api_url:copyright_policy_api')),
                              'skigit_for_business': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                     reverse(
                                                                         'aboutus_api_url:skigit_for_business_view_api')),
                              'business_verification': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                     reverse(
                                                                         'aboutus_api_url:business_verification_api')),
                              'business_service_fee': "{0}{1}".format(''.join(settings.HOST)[:-1],
                                                                      reverse(
                                                                          'aboutus_api_url:business_value_services_fees_api'))
                          })
            # return Response(result)

        except Exception as exc:
            logger.error("Helpful stuff api throws error: ", exc)
            result.update(status='error',
                          message='Your request is not successful. Please try later. Sorry for the inconvenience caused!',
                          data={})
        return Response(result)


class VideoDetailAPIView(generics.RetrieveAPIView):
    serializer_class = VideoDetailSerializer

    def get(self, request, pk):
        result = {'status': '',
                  'message': ''}
        data = request.query_params.copy()
        data.update(user_id=request.user.id if request.auth else 0)

        try:
            video_detail = get_object_or_None(VideoDetail, id=pk)
            serializer = self.get_serializer(video_detail)

            result.update(status='success',
                          message='',
                          data=serializer.data)
        except Exception as exc:
            logger.error("Serializer: VideoDetailAPIView:", exc)
            result.update(status='error',
                          message='Your request is not successful. Please try later. Sorry for the incovenience caused!',
                          data={})
        return Response(result)


class ProfileFriendDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (CustomIsAuthenticated,)
    serializer_class = ProfileFriendSerializer

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.query_params.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        friends = int(data.get('friends', 0))
        search_query = data.get('search_query', '').strip()
        friend_to_user = user_id if friends and friends != 0 else ''
        try:
            friends_detail = get_friends_list(friend_to_user, search_query=search_query)
            page = self.paginate_queryset(friends_detail)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_result = self.get_paginated_response(serializer.data)
                result.update(status='success',
                              message='',
                              data=paginated_result.data)

        except Exception as exc:
            logger.error("Serializer: ProfileFriendDetailAPIView:", exc)
            result.update(status='error',
                          message='Friends are not found!')
        return Response(result)


class VideoListAPIView(generics.ListAPIView):
    serializer_class = VideoDetailSerializer

    def list(self, request, videoId=None):
        result = {'status': '',
                  'message': ''}
        no_videos = 'No Skigits found!'
        data = request.query_params.copy()
        other_user_id = data.get('user_id', '')
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        type = data.get('type', 'home')
        video_id = data.get('video_id', '')
        cat_slug = data.get('cat_slug', '')
        sub_cat_slug = data.get('sub_cat_slug', '')
        sort_by = data.get('sort_by', '')
        order_by = data.get('order_by', 'desc')
        videos = []
        SORT_BY_DICT = {'title': 'title',
                        'date': 'created_date',
                        'like': 'like_count',
                        'view': 'view_count',
                        'random': '?'}
        ORDER_BY_DICT = {'desc': '-',
                         'asc': ''}

        try:
            if videoId is not None:
                videos = VideoDetail.objects.select_related('skigit_id').filter(
                    plugged_skigit_id=videoId,
                    status=1,
                    is_plugged=True,
                    is_active=True
                ).filter(
                    Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                ).order_by('-updated_date')
            elif type == 'home':
                videos = VideoDetail.objects.select_related('skigit_id').filter(status=1,
                                                                                is_active=True).filter(
                    Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                ).order_by('-updated_date')
            elif type == 'my_videos':
                if other_user_id:
                    videos = VideoDetail.objects.select_related('skigit_id').filter(
                        skigit_id__user__id=other_user_id,
                        status=1,
                        is_active=True
                    ).filter(
                        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                    ).order_by('-updated_date')
                elif user_id:
                    videos = VideoDetail.objects.select_related('skigit_id').filter(
                        skigit_id__user__id=user_id,
                        status=1,
                        is_active=True
                    ).filter(
                        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                    ).order_by('-updated_date')
            elif type == 'related_videos' and video_id:
                video = get_object_or_None(VideoDetail, id=video_id)
                if video:
                    related_user_list = get_related_users(user_id, video.skigit_id.user.id)
                    videos = VideoDetail.objects.exclude(id=video_id).filter(
                        Q(subject_category=video.subject_category) |
                        Q(skigit_id__user__in=related_user_list),
                        status=1, is_active=True).filter(
                        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                    ).order_by('?')
            elif type == 'embedded_videos':
                embed_user_id = None
                if other_user_id:
                    embed_user_id = other_user_id
                elif user_id:
                    embed_user_id = user_id
                if embed_user_id:
                    embed_videos = Embed.objects.filter(to_user__id=embed_user_id,
                                                        is_embed=True)
                    if embed_videos.exists():
                        embed_skigit_list = embed_videos.values_list('skigit_id', flat=True)
                        videos = VideoDetail.objects.select_related('skigit_id').filter(
                            skigit_id__id__in=embed_skigit_list).filter(
                                Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                            )
            elif type == 'category' and (sub_cat_slug or cat_slug):
                if sub_cat_slug:
                    category_current = get_object_or_None(SubjectCategory,
                                                          sub_cat_slug=sub_cat_slug,
                                                          is_active=True)
                    videos = VideoDetail.objects.select_related('skigit_id').filter(subject_category=category_current,
                                                                                    status=1,
                                                                                    is_active=True).filter(
                                        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                                    ).order_by('-updated_date')
                else:
                    category_current = get_object_or_None(Category,
                                                          cat_slug=cat_slug,
                                                          is_active=True)
                    videos = VideoDetail.objects.select_related('skigit_id').filter(category=category_current,
                                                                                    status=1,
                                                                                    is_active=True).filter(
                        Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
                    ).order_by('-updated_date')
            if sort_by and videos:
                if sort_by not in ['like', 'random']:
                    videos = videos.order_by('{0}{1}'.format(ORDER_BY_DICT[order_by],
                                                             SORT_BY_DICT[sort_by]))
                elif sort_by == 'random':
                    videos = videos.order_by('?')
                elif sort_by == 'like':
                    videoIds = [vid.skigit_id.id for vid in videos]
                    likes = Like.objects.filter(skigit_id__in=videoIds, status=True).values('skigit_id').annotate(
                        like_count=Count('skigit_id'))

                    likes = {l['skigit_id']: l['like_count'] for l in likes}
                    video_detail = []
                    for vid in videos:
                        vid.like_count = likes[vid.skigit_id.id] if vid.skigit_id.id in likes else 0
                        video_detail.append(vid)

                    desc = True if order_by == 'desc' else False
                    video_detail.sort(key=operator.attrgetter('like_count'), reverse=desc)
                    videos = video_detail
            page = self.paginate_queryset(videos)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_result = self.get_paginated_response(serializer.data)
                result.update(status='success',
                              message='',
                              data=paginated_result.data)
            else:
                result.update(status='success',
                              message=no_videos)
        except Exception as exc:
            logger.error("Serializer: VideoListView:", exc)
            result.update(status='error',
                          message='Videos list not found!')
        return Response(result)


class VideoLikeAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        video_id = data.get('video_id', '')
        like = int(data.get('like', 0))

        try:
            if like == 1:
                response = make_like(video_id, user_id)
            elif like == 0:
                response = make_unlike(video_id, user_id)
            else:
                response.update(is_success=False,
                                message="There is no like/unlike entry")
            status = 'success' if response['is_success'] else 'error'
            result.update(status=status,
                          message=response['message'])
        except Exception as exc:
            logger.error("Serializer: VideoLikeView:", exc)
            result.update(status='error',
                          message='Your request is not successful. Please try later. Sorry for the incovenience caused!')
        return Response(result)


class UserFollowAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        follow_id = data.get('follow_id', '')
        video_id = data.get('video_id', '')
        follow = int(data.get('follow', 0))

        try:
            if follow != 0:
                response = make_follow(follow_id, user_id, video_detail_id=video_id)
            else:
                response = make_unfollow(follow_id, user_id)
            status = 'success' if response['is_success'] else 'error'
            result.update(status=status,
                          message=response['message'])
        except Exception as exc:
            logger.error("Serializer: UserFollowView:", exc)
            result.update(status='error',
                          message='Your request is not successful. Please try later. Sorry for the incovenience caused!')
        return Response(result)


class VideoFavouriteAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request, video_id):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        favourite = int(data.get('favourite', 0))

        try:
            if favourite != 0:
                response = make_favourite(video_id, user_id)
            else:
                response = make_unfavourite(video_id, user_id)
            status = 'success' if response['is_success'] else 'error'
            result.update(status=status,
                          message=response['message'])
        except Exception as exc:
            logger.error("Serializer: VideoFavouriteAPIView:", exc)
            result.update(status='error',
                          message='Your request is not successful. Please try later. Sorry for the incovenience caused!',
                          data={})
        return Response(result)


class VideoStatisticsAPIView(views.APIView):

    def get(self, request, video_id):
        result = {'status': '',
                  'message': ''}
        try:
            response = manage_video_statistics(video_id)
            message = response['message']
            del response['message']
            result.update(status='success',
                          message=message,
                          data=response)
        except Exception as exc:
            logger.error("Serializer: VideoStatisticsAPIView:", exc)
            result.update(status='error',
                          message='Your request is not successful. Please try later. Sorry for the incovenience caused!')
        return Response(result)


class InappropriateReasonAPIView(generics.RetrieveAPIView):
    serializer_class = InappropriateReasonSerializer

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        try:
            all_reason = InappropriateSkigitReason.objects.all()
            serializer = self.get_serializer(all_reason, many=True)
            result.update(status='success',
                          message='',
                          data=serializer.data)
        except Exception as exc:
            logger.error("Serializer: InappropriateReasonAPIView:", exc)
            result.update(status='error',
                          message='Your request is not successful. Please try later. Sorry for the incovenience caused!')
        return Response(result)


class VideoFlagAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request, video_id):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        flag_reason_id = data.get('flag_reason_id', '')

        try:
            response = manage_flag_video(video_id, user_id, flag_reason_id)
            status = 'success' if response['is_success'] else 'error'
            result.update(status=status,
                          message=response['message'])
        except Exception as exc:
            logger.error("Serializer: VideoFlagAPIView:", exc)
            result.update(status='error',
                          message='This Skigit is not flagged successfully. Please try again later.')
        return Response(result)


class VideoShareAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        video_id = data.get('video_id', '')
        time_zone = data.get('time_zone', '')
        friend_list = data.get('friend_list', [])
        email_list = data.get('email_list', [])
        share_type = data.get('type', 'friends')

        try:
            if share_type == 'friends':
                response = manage_share_video(user_id, time_zone, video_id, friend_list)
            else:
                response = manage_share_video_to_email(user_id, video_id, email_list)
            status = 'success' if response['is_success'] else 'error'
            result.update(status=status,
                          message=response['message'])
        except Exception as exc:
            logger.error("Serializer: VideoShareAPIView:", exc)
            result.update(status='error',
                          message='This Skigit is not shared successfully. Please try again later.')
        return Response(result)


class CopyrightInfringementAPIView(generics.CreateAPIView):
    serializer_class = CopyrightInfringementSerializer
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request, video_id):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        submitter_request = int(data.get('submitter_request', 0))
        submitter_request = True if submitter_request == 1 else False
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id,
                    skigit_id=video_id,
                    submitter_request=submitter_request)

        try:
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                copy_right = serializer.save()
                result.update(status='success',
                              message='A Copyright Infringement claim has been submitted!')
            else:
                result.update(get_error_result(serializer.errors))
        except Exception as exc:
            logger.error("Serializer: CopyrightInfringementAPIView:", exc)
            result.update(status='error',
                          message='A Copyright Infringement claim is not successful. Please check the inputs. {}'.format(
                              str(exc)))
        return Response(result)


class DonateGroupsAPIView(generics.ListAPIView):
    permission_classes = (CustomIsAuthenticated,)
    serializer_class = DonationSerializer

    def get(self, request):
        result = {'status': '',
                  'message': ''}

        donate_groups = Donation.objects.all()
        try:
            serializer = self.get_serializer(donate_groups, many=True)
            result.update(status='success',
                          message='',
                          data=serializer.data)
        except Exception as exc:
            logger.error("Serializer: DonateGroupsAPIView:", exc)
            result.update(status='error',
                          message='There are no Donate Groups')
        return Response(result)


class VideoUploadInitAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        data = {}

        try:
            category = Category.objects.all()
            category_serializer = CategorySerializer(category, many=True)
            subject_category = SubjectCategory.objects.all()
            subject_category_serializer = SubjectCategorySerializer(subject_category, many=True)
            business_user = User.objects.filter(groups__name=settings.BUSINESS_USER,
                                                invoice_user__type__in=['PayPalAccount', 'CreditCard'],
                                                invoice_user__is_deleted=False).distinct('username')
            business_profile = Profile.objects.filter(user__id__in=business_user.values_list('id', flat=True),
                                                      payment_method__isnull=False,
                                                      payment_email__isnull=False).distinct('company_title'). \
                order_by('company_title')
            business_user_serializer = BusinessProfileDetailSerializer(business_profile, many=True)
            data.update(category=category_serializer.data,
                        subject_category=subject_category_serializer.data,
                        business_user=business_user_serializer.data)

            result.update(status='success',
                          message='',
                          data=data)
        except Exception as exc:
            logger.error("Serializer: VideoUploadInitAPIView:", exc)
            result.update(status='error',
                          message="The video upload couldn't initialize")
        return Response(result)


class VideoUploadAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}

        try:
            data = request.data
            request.POST._mutable= True  # Enable mutable so that request data can be modified
            data['title'] = string.capwords(data['title'])  # Capitalize first letter of each word
            user_id = request.user.id if request.auth else 0
            # data.update(user_id=user_id)
            files = request.FILES
            serializer = VideoUploadSerializer(data=data)
            if serializer.is_valid():
                upload_type = data.get('type', 'new')
                if upload_type == 'new':
                    response = manage_upload_video(user_id, data, files=files)
                elif upload_type == 'plugin':
                    response = manage_plugin_upload_video(user_id, data, files=files)
                if response.get('is_success', False):
                    status = 'success'
                    response.update(
                        message="Your video was successfully uploaded and you will be notified when posted.")
                else:
                    status = 'error'
                message = response['message'] if response.get('message', '') else ''
                result.update(status=status,
                              message=message)
            else:
                result.update(get_error_result(serializer.errors))
        except Exception as exc:
            logger.error("Serializer: VideoUploadAPIView:", exc)
            result.update(status='error',
                          message='The video is not uploaded successfully!')
        return Response(result)


class VideoPluginAPIView(views.APIView):
    '''
        Upload plugin video
    '''

    permission_classes = (CustomIsAuthenticated,)

    def post(self, request, plug_id):
        result = {'status': '',
                  'message': ''}

        try:
            data = request.data
            data['title'] = string.capwords(data['title'])  # Capitalize first letter of each word
            serializer = VideoUploadSerializer(data=data)
            if serializer.is_valid():
                response = manage_plugin_upload(plug_id, data)
                status = 'success' if response.get('is_success', True) else 'error'
                message = response['message'] if response.get('message', '') else ''
                result.update(status=status,
                              message=message)
            else:
                result.update(get_error_result(serializer.errors))
        except Exception as exc:
            logger.error("Serializer: Video Plugin upload:", exc)
            result.update(status='error',
                          message='The video plugin is not uploaded successfully!')
        return Response(result)


class VideoSearchAPIView(generics.ListAPIView):
    queryset = VideoDetail.objects.all()
    serializer_class = VideoDetailSerializer
    pagination_class = PageNumberPagination

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        try:
            request_data = request.query_params
            vid = manage_video_search(request_data)
            page = self.paginate_queryset(vid)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_result = self.get_paginated_response(serializer.data)
                data = paginated_result.data
            else:
                serializer = self.get_serializer(vid, many=True)
                data = serializer.data
            result.update(status='success',
                          message='',
                          data=data)
        except Exception as exc:
            logger.error("Serializer: VideoSearchAPIView:", exc)
            result.update(status='error',
                          message='Search result is empty.')
        return Response(result)


class VideoDeleteAPIView(views.APIView):
    '''
        Delete video API
    '''

    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}

        try:
            data = request.data.copy()
            user_id = request.user.id if request.auth else 0
            data.update(user_id=user_id)
            video_id = data.get('video_id', '')
            response = mark_video_as_deleted(user_id, video_id)
            status = 'success' if response.get('is_success', True) else 'error'
            message = response['message'] if response.get('message', '') else ''
            result.update(status=status,
                          message=message)
        except Exception as exc:
            logger.error("Serializer: Video Delete:", exc)
            result.update(status='error',
                          message='The video is not deleted successfully!')
        return Response(result)


class UnPlugVideoView(views.APIView):
    '''
        Unplug video!
    '''

    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}

        try:
            data = request.data.copy()
            user_id = request.user.id if request.auth else 0
            data.update(user_id=user_id)
            video_id = data.get('video_id', '')
            response = unplug_video(user_id, video_id)
            status = 'success' if response.get('is_success', True) else 'error'
            message = response['message'] if response.get('message', '') else ''
            result.update(status=status,
                          message=message)
        except Exception as exc:
            logger.error("Serializer: Video Un-Plug:", exc)
            result.update(status='error',
                          message='The video is not un-plugged successfully!')
        return Response(result)


class ShareSocialnetworkAPIView(views.APIView):
    '''
        Share content to social networks!.
        If it has video_id, share the video content
        Otherwise general site content
    '''
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.query_params
        video_id = data.get('video_id', '')

        try:
            share_data = {}
            if video_id:
                video_detail = get_object_or_None(VideoDetail, id=video_id)

                share_data.update(id=video_id,
                                  title=video_detail.title,
                                  description=video_detail.why_rocks,
                                  share_image_url=get_video_share_image_url(video_id),
                                  share_url='{}{}'.format(settings.HOST,
                                                          reverse('skigit_data', kwargs={'pk': video_id})))
            else:
                share_data.update(title='Skigit',
                                  description='',
                                  share_image_url="{0}images/logo_og.png".format(settings.STATIC_URL),
                                  share_url='{}{}'.format(settings.HOST,
                                                          reverse('index')))

            result.update(status='success',
                          message='',
                          data=share_data)
        except Exception as exc:
            logger.error("Serializer: Share Socialnetwork:", exc)
            result.update(status='error',
                          message='Sharing is failed. Please try later.',
                          data={})
        return Response(result)


def get_plugin_videos(skigit_id):
    return VideoDetail.objects.filter(
        plugged_skigit_id=skigit_id,
        status=1,
        is_plugged=True,
        is_active=True
    ).order_by('?').select_related('skigit_id').filter(status=1, is_active=True).filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        )


def fetch_plugins_with_position(video_id):
    videos_latest = get_plugin_videos(video_id)[:8]

    videos_list = []
    for video in videos_latest:
        related_plugins = get_plugin_videos(video.skigit_id)
        video.second_level_plugins = related_plugins[:8]
        video.second_level_plugins_count = related_plugins.count()
        videos_list.append(video)

    return videos_list

@login_required(login_url='/login')
def get_state_list(request):
    country = request.GET.get('country')
    context = {
        'state_list': states_list_By_country(country),
    }
    return JsonResponse(context)


class SkigitPluginMapApiView(generics.ListAPIView):
    # permission_classes = (CustomIsAuthenticated,)
    serializer_class = PluginVideoSerializer

    def get(self, request, video_id):
        result = {'status': '',
                  'message': ''}
        try:
            plugins = fetch_plugins_with_position(video_id)
            page = self.paginate_queryset(plugins)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_result = self.get_paginated_response(serializer.data)
                result.update(status='success',
                              message='',
                              data=paginated_result.data)
            else:
                result.update(status='success',
                              message='No plugin skigits found!')
        except Exception as exc:
            logger.error("Plugin map error - :", exc)
            result.update(status='error',
                          message='Plugin map error',
                          data={})
        return Response(result)


class VideoTitleExistView(View):
    """
        Return the title exist or not!
    """

    def get(self, request):
        """
        Return "true" if exist or throws error message
        """
        error_message = "Title is already used. Please enter different one."
        title = self.request.GET.get('title', '').strip()
        title_exists = VideoDetail.objects.filter(title__iexact=title).exists()
        message = error_message if title_exists else "true"
        return JsonResponse(message, safe=False)
