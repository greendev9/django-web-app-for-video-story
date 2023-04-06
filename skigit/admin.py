from asyncio.log import logger
from user.models import Profile, BusinessDoc

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission, User
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db import models
from django.urls import reverse
from social.models import Follow
from tinymce.widgets import TinyMCE
from django.conf import settings
from django.template.defaultfilters import safe

from core.utils import (trigger_send_email, is_user_business)
from core.emails import coupan_email, send_email
from core.models import Category, SubjectCategory
from core.youtube_upload import delete_video
from friends.models import Notification
from friends.views import notification_settings
from invoices.views import business_plug_invoice, updateMonthlySkigitInvoice, business_donate_invoice
from skigit.models import (BugReport, CopyRightInfringement, CopyRightInvestigation, InappropriateSkigit,
                           InappropriateSkigitInvestigator, InappropriateSkigitReason, Payment, Thumbnail, Video,
                           VideoDetail)
from skigit.storage import B2Storage
from skigit_project.settings import EMAIL_HOST_BUSINESS, EMAIL_HOST_COPYRIGHT, EMAIL_HOST_VIDEO
from sperks.models import Donation, Incentive
from mailpost.models import EmailTemplate
from .managers import VideoDetailManagerAdmin
from django.utils import timezone
import datetime
from django.utils.html import format_html

admin.site.disable_action('delete_selected')

# Reverse to default actions position overriding suit config
admin.ModelAdmin.actions_on_top = True
admin.ModelAdmin.actions_on_bottom = False


def approve_video(video_detail_obj, admin_user=None):
    """

    :param video_detail_obj:
    :param admin_user: reuest user if not default super admin user!
    :return:
    """

    http_host = settings.WWW_HOST
    email_template_key_user = None
    email_template_key_business = None
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True, is_active=True)[0]
    if not video_detail_obj.status == 1:
        # if not video_detail_obj.status == 1 and not video_detail_obj.inappropriate_skigit == '2':
        video_detail_obj.status = 1
        video_detail_obj.published_at = timezone.now()
        video_detail_obj.deleted_at = None
        video_detail_obj.save()

        if video_detail_obj.incentive and not video_detail_obj.incentive.is_paid:
            video_detail_obj.incentive.is_active = True
            video_detail_obj.incentive.billing_month = datetime.datetime.now().date()
            video_detail_obj.incentive.save()

        if video_detail_obj.plugged_skigit:
            vid_obj = VideoDetail.objects.get(skigit_id=video_detail_obj.plugged_skigit.id)
            if notification_settings(video_detail_obj.skigit_id.user.id, 'plug_notify'):
                if not vid_obj.is_plugged:
                    msg_type = 'plug'
                    plug_message = 'Congratulations! '
                    plug_message += vid_obj.skigit_id.user.username
                    plug_message += ' has plugged into your Skigit '
                    plug_message += vid_obj.title
                else:
                    msg_type = 'plug-plug'
                    plug_message = 'Coincidence? I think not! '
                    plug_message += video_detail_obj.skigit_id.user.username
                    plug_message += ' has plugged into a Skigit that you plugged into '
                    plug_message += vid_obj.title
                Notification.objects.create(msg_type=msg_type, skigit_id=vid_obj.skigit_id.id,
                                            user=vid_obj.skigit_id.user, message=plug_message,
                                            from_user=video_detail_obj.skigit_id.user)
                EmailTemplate.send(
                template_key="your_skigit_was_plugged",
                emails=video_detail_obj.skigit_id.user.email,
                context={
                    "username": vid_obj.skigit_id.user.username,
                    "title": vid_obj.title,
                    "skigit_id": vid_obj.id,
                    "host": ''.join(settings.HOST)[:-1]
                })
                
            if vid_obj.made_by:
                if not video_detail_obj.skigit_id.user.id == vid_obj.made_by.id:
                    business_plug_invoice(None, video_detail_obj.id, video_detail_obj.skigit_id.user.id, vid_obj.id,
                                          vid_obj.made_by.id)

        # Notification for New Post Skigit.
        ski_nt_message = " Congratulations! Your Skigit %s has been posted to Skigit! " % video_detail_obj.title
        ski_follower_message = " Following Post! %s has posted a new skigit %s" % (video_detail_obj.skigit_id.user,
                                                                                    video_detail_obj.title)
        if notification_settings(video_detail_obj.skigit_id.user.id, 'skigit_notify'):
            if not Notification.objects.filter(msg_type='new_post', skigit_id=video_detail_obj.skigit_id.id,
                                               user=video_detail_obj.skigit_id.user, from_user=admin_user).exists():
                Notification.objects.create(msg_type='new_post', skigit_id=video_detail_obj.skigit_id.id,
                                            user=video_detail_obj.skigit_id.user, from_user=admin_user,
                                            message=ski_nt_message)
            # notify followers
            followers = Follow.objects.filter(follow=video_detail_obj.skigit_id.user, status=True).select_related('user')
            for follower in followers:
                if video_detail_obj.skigit_id.user.id != follower.user.id and notification_settings(follower.user.id, 'skigit_notify'):
                    Notification.objects.create(msg_type='new_post_follow', skigit_id=video_detail_obj.skigit_id.id,
                                                user=follower.user, from_user=video_detail_obj.skigit_id.user,
                                                message=ski_follower_message)

            # Accept Skigit Email Message Body only if it's not a sperk
            if not video_detail_obj.incentive and not video_detail_obj.donate_skigit and (video_detail_obj.receive_donate_sperk not in [1,2]  or not video_detail_obj.business_logo):
                EmailTemplate.send(
                    template_key="your_skigit_was_posted",
                    emails=video_detail_obj.skigit_id.user.email,
                    context={
                        "skigit_id": video_detail_obj.id,
                        "title": video_detail_obj.skigit_id.title,
                        "host": ''.join(settings.HOST)[:-1]
                    })

        updateMonthlySkigitInvoice(video_detail_obj, 'approved')
        if video_detail_obj.business_logo is not None:
            user_profile = Profile.objects.filter(logo_img=video_detail_obj.business_logo.id).first()
            receive_donate_sperk = int(video_detail_obj.receive_donate_sperk)
            business_logo = video_detail_obj.business_logo
            creator = video_detail_obj.skigit_id

            # For Receive sperk
            if receive_donate_sperk == 1 and business_logo:
                email_template_key_user = "redeem_your_sperk_business"
                email_template_key_business = "user_receive_skitbit_to_business"
            # For donate sperk
            elif receive_donate_sperk == 2 and business_logo:
                if video_detail_obj.donate_skigit is not None:
                    email_template_key_user = "redeem_your_sperk_user_donate"
                    email_template_key_business = "user_donate_skitbit_to_business"
                if video_detail_obj.made_by:
                    incentive_amount = user_profile.incetive_val
                    if incentive_amount:
                        business_donate_invoice(user_profile.user.id, video_detail_obj.id, incentive_amount)

            if email_template_key_business and user_profile.incentive == 1:
                creator_context = {}
                image_url = "{}/{}".format(http_host, business_logo.logo.url)
                company_title = user_profile.company_title
                instruction = user_profile.redemoption_instrucations
                incentive_txt = user_profile.skigit_incentive
                profile_name = '%s/%s/' % (video_detail_obj.made_by.id, business_logo.id)
                username = creator.user.get_full_name() if creator.user.get_full_name() else \
                            creator.user.username
                coupon_url = '{0}{1}'.format(settings.MEDIA_HOST_URL, user_profile.coupan_image) if user_profile.coupan_image else ''
                user_context = {
                    "company_title": company_title,
                    "profile_name": profile_name,
                    "image_url": image_url,
                    "skigit_id": video_detail_obj.id,
                    "title": creator.title,
                    "username": username,
                    "incetive_val": user_profile.incetive_val,
                    "host": ''.join(settings.HOST)
                    
                }

                creator_context.update(user_context)
                creator_context.update({
                    "insentive_txt": incentive_txt
                })

                if receive_donate_sperk == 1:
                    user_context.update({"insentive_txt": incentive_txt,
                                         "instruction": instruction,
                                         "coupan_url": coupon_url})
                    creator_context.update({"coupan_url": coupon_url,
                                          "instruction": instruction})
                else:
                    user_context.update({"ngo_name": video_detail_obj.donate_skigit.ngo_name})
                    creator_context.update({"url": video_detail_obj.donate_skigit.url,
                                            "ngo_name": video_detail_obj.donate_skigit.ngo_name})
                trigger_send_email(email_template_key_user,
                                   to_email=[creator.user.email],
                                   context=user_context)
                trigger_send_email(email_template_key_business,
                                   to_email=[user_profile.user.email],
                                   context=creator_context)
            else:
              # Send email to business because user creates a non-skitbit skigit
              if video_detail_obj.made_by and business_logo:
                  email_template_key_business = "user_nonskitbit_to_business"
                  profile_name = '%s/%s/' % (video_detail_obj.made_by.id, business_logo.id)
                  trigger_send_email(email_template_key_business,
                                       to_email=[user_profile.user.email],
                                      context={
                                              "skigit_id": video_detail_obj.id,
                                              "title": video_detail_obj.skigit_id.title,
                                              "company_title": user_profile.company_title,
                                              "profile_name": profile_name,
                                              "host": ''.join(settings.HOST)
                                      }
                                    )



def unapprove_video(video_detail_obj, template_key='your_skigit_was_rejected', request_user=None):
    """
        Args: video_detail_obj

        Returns:  Video Statusr from Publish or Pending to Reject
    """
    # if not obj.status == 2 and not obj.inappropriate_skigit:
    video_detail_obj.status = 2
    video_detail_obj.save()

    # deactivate incentive on rejected
    if video_detail_obj.incentive:
        video_detail_obj.incentive.is_active = False
        video_detail_obj.incentive.save()

    EmailTemplate.send(
        template_key=template_key,
        emails=video_detail_obj.skigit_id.user.email,
        context={
            "title": video_detail_obj.skigit_id.title,
            "id": video_detail_obj.id,
            "host": ''.join(settings.HOST)
        }
    )

    ski_nt_message = " Your Skigit %s has been rejected for posting. " % video_detail_obj.title
    if notification_settings(video_detail_obj.skigit_id.user.id, 'skigit_notify') == True:
        if not Notification.objects.filter(msg_type='unapproved', skigit_id=video_detail_obj.skigit_id.id,
                                           user=video_detail_obj.skigit_id.user, from_user=request_user).exists():
            Notification.objects.create(msg_type='unapproved', skigit_id=video_detail_obj.skigit_id.id,
                                        user=video_detail_obj.skigit_id.user, from_user=request_user,
                                        message=ski_nt_message)


class FlatPageForm(forms.ModelForm):
    """
        Flat Page Form
    """

    class Meta:
        model = FlatPage
        widgets = {
            'content': TinyMCE(attrs={'cols': 100, 'rows': 15}),
        }
        fields = '__all__'


class PageAdmin(FlatPageAdmin):
    """
        Page Admin
    """
    form = FlatPageForm


admin.site.unregister(FlatPage)


class CategoryInline(admin.ModelAdmin):
    """
        Category Inline
    """
    model = Category
    prepopulated_fields = {'cat_slug': ('cat_name',)}
    extra = 3


class SubjectCategoryInline(admin.ModelAdmin):
    """
        Subject Category Inline
    """
    model = SubjectCategory
    extra = 3
    prepopulated_fields = {'sub_cat_slug': ('sub_cat_name',)}


class ThumbnailInline(admin.StackedInline):
    """
        Thumbnail Inline
    """
    model = Thumbnail
    fk_name = 'video'
    extra = 0


class VideoAdmin(admin.ModelAdmin):
    """
        Video Admin
    """
    readonly_fields = ('video_id', 'youtube_url', 'swf_url',)
    inlines = [ThumbnailInline]
    list_filter = ('title', 'user__username',)
    search_fields = ['title', 'user__first_name', 'user__email', 'user__username']

    list_display = ('title', 'video_id', 'swf',)

    def swf(self, instance):
        """
            Args:
                instance: Object of Video
            Returns: SWF Video Link
        """
        return format_html('<a href="%s">Swf link</a>' % (instance.get_absolute_url()))

    swf.allow_tags = True



class IncentiveAdmin(admin.ModelAdmin):
    """
        Video Admin
    """
    list_filter = ('sperk_type', 'is_active', 'user__username',)
    search_fields = ['title', 'billing_month', 'is_active', 'user__first_name', 'user__email', 'user__username']

    list_display = ('skigit_title', 'sperk_type', 'amount', 'billing_month', 'business_user', 'is_active')

    def business_user(self, obj):
        user_link = '--'
        if obj.user is not None:
            user_link = format_html('<a href="/admin/auth/user/{}/change" >{}</a>'.format(obj.user.id, obj.user.email))
        return user_link

    business_user.allow_tags = True

    def has_add_permission(self, request, obj=None):
        # Disable delete
        return False

    def skigit_title(self, obj):
        skigit_title = '--'
        if obj.videodetail_set.exists():
            skigit = obj.videodetail_set.first()
            skigit_title = format_html('<a href="/admin/sperks/incentive/{}/change/" >{}</a>'.format(obj.id, skigit.title))
        else:
            skigit_title = obj.title
        return skigit_title

    skigit_title.allow_tags = True

class VideoDetailAdmin(admin.ModelAdmin):
    """
        Video Detail Admin
    """
    model = VideoDetail
    fk_name = 'skigit_id'
    readonly_fields = ('id', 'title', 'get_inappropriate_skigit', 'get_status',)
    list_display = ('id', 'related_skigit_title', 'get_status', 'get_inappropriate_skigit','get_copy_right_skigit',
                    'is_deleted', 'link_related_swf', 'related_skigit_category', 'related_user', 'made_by', 'views',
                    'likes', 'get_plugin_video', 'created_date')
    list_filter = ('category', 'status', 'inappropriate_skigit', 'created_date')
    actions = ['approve', 'unapprove', 'mark_as_deleted', 'delete_model', ]
    search_fields = ['skigit_id__title', 'made_by__username', 'made_by__first_name', 'skigit_id__user__username',
                     'skigit_id__user__first_name', 'plugged_skigit__title', 'category__cat_name']
    ordering = ('status', '-created_date')

    def get_queryset(self, request):
        return VideoDetail.all_objects.all()

    list_per_page = 15

    def get_plugin_video(self, obj):
        """
            Get Plugin Videos
        """
        if obj.plugged_skigit:
            if obj.plugged_skigit:
                return obj.plugged_skigit.title
            return ''
        return ''

    get_plugin_video.allow_tags = True
    get_plugin_video.short_description = 'plugged Skigit'
    get_plugin_video.admin_order_field = 'plugged_skigit__title'

    def get_inappropriate_skigit(self, obj):
        """
            Get Inappropriate Skigit
        """

        if obj.inappropriate_skigit:
            inappropriates = InappropriateSkigit.objects.filter(skigit_id=obj.id)
            to_return = '<ul>'
            for item in inappropriates:
                if item.action == '0':
                    link = format_html('<a href="/admin/skigit/inappropriateskigit/{}/change/" target="_blank">' \
                           '<span style="color:orange;">Pending</span></a>'.format(item.id))
                    to_return += '<li>{}</li>'.format(link)
                elif item.action == '1':
                    link = format_html('<a href="/admin/skigit/inappropriateskigit/{}/change/" target="_blank">' \
                           '<span style="color:green;">Appropriate</span></a>'.format(item.id))
                    to_return += '<li>{}</li>'.format(link)
                elif item.action == '2':
                    link = format_html('<a href="/admin/skigit/inappropriateskigit/{}/change/" target="_blank">' \
                           '<span style="color:red;">Inappropriate</span></a>'.format(item.id))
                    to_return += '<li>{}</li>'.format(link)
            to_return += '</ul>'
            return to_return
        else:
            return ''

    get_inappropriate_skigit.allow_tags = True
    get_inappropriate_skigit.short_description = 'Inappropriate Skigit'
    get_inappropriate_skigit.admin_order_field = 'inappropriate_skigit'

    def get_copy_right_skigit(self, obj):
        """
            Get Copyright Skigit
        """

        if obj.copyright_skigit:
            cp = CopyRightInfringement.objects.filter(skigit_id=obj.id)
            to_return = '<ul>'
            for item in cp:
                if item.status == 0 or item.status == 1:
                    link = format_html('<a href="/admin/skigit/copyrightinfringement/{}/change/" target="_blank">' \
                           '<span style="color:orange;">Under Investigation</span></a>'.format(item.id))
                    to_return += '<li>{}</li>'.format(link)
                elif item.status == 2:
                    link = format_html('<a href="/admin/skigit/copyrightinfringement/{}/change/" target="_blank">' \
                           '<span style="color:green;">Closed</span></a>'.format(item.id))
                    to_return += '<li>{}</li>'.format(link)
                elif item.status == 3:
                    link = format_html('<a href="/admin/skigit/copyrightinfringement/{}/change/" target="_blank">' \
                           '<span style="color:red;">Remove Skigit</span></a>'.format(item.id))
                    to_return += '<li>{}</li>'.format(link)
            to_return += '</ul>'
            return to_return
        else:
            return ''

    get_copy_right_skigit.allow_tags = True
    get_copy_right_skigit.short_description = 'Copyright Infringement'
    get_copy_right_skigit.admin_order_field = 'copyright_skigit'

    def related_skigit_category(self, obj):
        """
            Args:
                obj: Video Instance
            Returns: Category Name
        """
        return obj.category.cat_name

    related_skigit_category.short_description = 'Category'

    def is_deleted(self, obj):
        """
            Is Delete Status
        """
        if obj.is_active:
            return False
        else:
            return True

    is_deleted.boolean = True
    is_deleted.short_description = 'Deleted by User'

    @staticmethod
    def views(obj):
        """
            Vievs count
        """
        return obj.view_count

    def get_status(self, obj):
        """
            Get Status
        """
        if obj.status == 0:
            return format_html('<p style="color:#F39C12">Pending</p>')
        elif obj.status == 1:
            return format_html('<p style="color:#1E8449">Publish</p>')
        elif obj.status == 2:
            return format_html('<p style="color:#FF0000">Rejected</p>')
        elif obj.status == 3:
            return format_html('<p style="color:#FF0000">Deleted</p>')

    get_status.allow_tags = True
    get_status.short_description = 'Status'
    get_status.admin_order_field = 'status'

    @staticmethod
    def likes(obj):
        """
            Args:
                obj: Instance

            Returns: Likes count
        """
        return obj.skigit_id.likes.filter(status=True).count()

    # def related_swf(self, obj):
    #     """
    #         Args:
    #             obj: Instance
    #         Returns: SWF Url
    #     """
    #     return '<a href="https://www.youtube.com/my_videos?o=U" target="_blank">Show</a>'
    # related_swf.allow_tags = True
    # related_swf.short_description = 'Video Link'

    def link_related_swf(self, obj):
        """
            Args:
                obj: Instance
            Returns: Url Of Youtube Video List Page
        """
        return format_html('<a href="{0}" target="_blank">{0}</a>'.format(obj.skigit_id.get_absolute_url()))

    link_related_swf.allow_tags = True
    link_related_swf.short_description = 'Video URL'

    def related_user(self, obj):
        """
            Args:
                obj: Instance
            Returns: User Name
        """
        return obj.skigit_id.user

    related_user.short_description = 'User Name'

    def related_skigit_title(self, obj):
        """
            Args:
                obj: Instance
            Returns: Video Title
        """
        return obj.skigit_id.title

    related_skigit_title.short_description = 'Primary Skigit'

    def approve(self, request, queryset):
        """
            Args:
                request: Instance
                queryset: obj
            Returns: Video Status As Publish and send's email related users
        """
        for obj in queryset:
            approve_video(obj, request.user)

    approve.short_description = "Mark selected Skigit as Publish"

    def unapprove(self, request, queryset):
        """
            Args:
                request: requested user
                queryset: obj
            Returns:  Video Statusr from Publish or Pending to Reject
        """
        for obj in queryset:
            # if not obj.status == 2 and not obj.inappropriate_skigit:
            if not obj.status == 2:
                unapprove_video(obj, request_user=request.user)
            elif obj.status == 2 and not obj.inappropriate_skigit:
                obj.status = 2
                obj.save()

    unapprove.short_description = "Mark selected Skigit as Reject"

    def save_model(self, request, obj, form, change):
        
        obj.save()

        try:
            old_status = VideoDetail.objects.get(id=obj.id).status if change else 0
            if old_status != 1 and obj.status == 1:
                # Notification for New Post Skigit.
                ski_nt_message = " Congratulations! Your Skigit %s has been posted to Skigit! " % obj.title
                ski_follower_message = " Following Post! %s has  posted a new skigit %s" % (obj.skigit_id.user,
                                                                                            obj.title)
                if notification_settings(obj.skigit_id.user.id, 'skigit_notify'):
                    if not Notification.objects.filter(msg_type='new_post', skigit_id=obj.skigit_id.id,
                                                    user=obj.skigit_id.user,
                                                    from_user=request.user).exists():
                        Notification.objects.create(msg_type='new_post', skigit_id=obj.skigit_id.id,
                                                    user=obj.skigit_id.user,
                                                    from_user=request.user, message=ski_nt_message)

                    # notify followers
                    followers = Follow.objects.filter(follow=obj.skigit_id.user, status=True).all()
                    for follower in followers:
                        if obj.skigit_id.user.id != follower.user.id and notification_settings(follower.user.id, 'skigit_notify'):
                            Notification.objects.create(msg_type='new_post_follow', skigit_id=obj.skigit_id.id,
                                                        user=follower.user, from_user=obj.skigit_id.user,
                                                        message=ski_follower_message)
        except:
            logger.error("------error-------")
    def delete_model(self, request, queryset):
        """
            Args:
                request: requested users
                queryset:obj
            Returns: 1 on video deleted as Success
        """
        b2 = B2Storage()
        if isinstance(queryset, VideoDetail):
            video = Video.objects.get(pk=queryset.skigit_id.id)
            video.delete()
        else:
            for obj in queryset:
                video = Video.objects.get(pk=obj.skigit_id.id)
                video.delete()

    delete_model.short_description = "Delete Skigit (Permanent)"

    def mark_as_deleted(self, request, queryset):
        for obj in queryset:
            Notification.objects.filter(skigit=obj.skigit_id).delete()

        queryset.update(status=3, deleted_at=timezone.now())

    mark_as_deleted.short_description = "Delete Skigit (Temporarily)"

admin.site.unregister(User)

class BusinessDocInlineForm(forms.ModelForm):
    business_doc = forms.ModelMultipleChoiceField(
                    queryset=BusinessDoc.objects.all(),
                    widget=forms.CheckboxSelectMultiple(),
                    required=False,
                    disabled=True)
    class Meta:
        model = Profile
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(BusinessDocInlineForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.fields['business_doc'].queryset = kwargs['instance'].business_doc.all()
            self.fields['business_doc'].widget.choices = [(doc.id, safe("<a href='{}'>{}</a>".format(doc.doc.url, doc.doc.url))) for doc in
                                                             kwargs['instance'].business_doc.all()]


class ProfileInline(admin.StackedInline):
    """
        Profile Inline Admin
    """
    form = BusinessDocInlineForm
    model = Profile
    fk_name = 'user'


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields[
            'is_active'].help_text = 'Designates whether this user account is active. Selecting' \
                                     ' this will restore the account and all previous' \
                                     ' Skigits statistics, connections, and user data.'

    class Meta:
        model = User
        exclude = ()


class UserProfileAdmin(UserAdmin):
    form = UserForm
    """
        User Profile Admin
    """
    list_display = ('username', 'verified_business', 'reject_request', 'email', 'first_name', 'last_name', 'is_active', 'get_is_staff', 'get_video_rights',
                    'get_payment_rights', 'get_bug_rights', 'get_inappropriate_rights', 'get_copy_rights',
                    'date_joined')
    actions = ['assing_video_management', 'remove_video_management', 'assing_payment_management',
               'remove_payment_management', 'assign_copyright_management', 'remove_copyright_management',
               'assign_bug_management', 'remove_Bug_management', 'assign_inappropriate_management',
               'remove_inappropriate_management', 'add_all_rights', 'remove_all_rights', 'delete_selected']
    list_filter = ('is_superuser', 'is_active', 'groups', 'date_joined',)
    inlines = [ProfileInline, ]

    def verified_business(self, obj):

        if obj.id:
            p_obj = Profile.objects.get(user=obj.id)

            if is_user_business(obj): #checking whether user is business user
                if p_obj.business_verified:
                    return format_html("<input type='checkbox' name='"+ str(p_obj.user_id) +"' id='"+ str(p_obj.user_id) +"' onclick='business_verified("+str(p_obj.user_id)+")' checked><label for='"+ str(p_obj.user_id) +"'></label>")
                else:
                    return format_html("<input type='checkbox' name='"+ str(p_obj.user_id) +"' id='"+ str(p_obj.user_id) +"' onclick='business_verified("+str(p_obj.user_id)+")'><label for='"+ str(p_obj.user_id) +"'></label>")

    verified_business.short_description = "Verified"
    
    def reject_request(self, obj):
        
        if obj.id:
            p_obj = Profile.objects.get(user=obj.id)

            if is_user_business(obj):#checking whether user is business user

                #if not p_obj.business_verified :# and deadline for acception
                    #return format_html("<button class='reject_btn' style='margin-left:3px; width: 60px' type='button' id='"+ str(p_obj.user_id) +"_btn' onclick='rejectEmail("+ str(p_obj.user_id) +")' >Reject</button>")
                    return format_html("<select class='reject_btn' style='margin-left:3px; width: 60px' id='"+ str(p_obj.user_id) +"_btn' onchange='rejectEmail(" + str(p_obj.user_id) + ")' >"+\
                                        "<option value='-'>-</option>"+\
                                        "<option value='Documents you submitted are not an accepted type'>Documents you submitted are not an accepted type</option>"+\
                                        "<option value='Submission incomplete'>Submission incomplete</option>"+\
                                        "<option value='Document language is unsupported'>Document language is unsupported</option>"+\
                                        "<option value='Document isn&#39;t viewable'>Document isn't viewable</option>"+\
                                        "<option value='Document is expired'>Document is expired</option>"+\
                                        "<option value='Document doesn&#39;t contain legal business name'>Document doesn't contain legal business name</option>"+\
                                        "<option value='Name on document doesn&#39;t match business name'>Name on document doesn't match business name</option>"+\
                                        "<option value='Document doesn&#39;t contain a buiness address, onlya partial, or doesn&#39;t match your business address'>Document doesn't contain a buiness address, onlya partial, or doesn't match your business address</option>"+\
                                        "<option value='Document doesn&#39;t contain a buiness pbone number or doesn&#39;t match your business phone number'>Document doesn't contain a buiness pbone number or doesn't match your business phone number</option>"+\
                                        "<option value='Additional documents required for verification'>Additional documents required for verification</option>"+\
                                        "<option value='You own your website domain but aren&#39;t making it through verification'>You own your website domain but aren't making it through verification</option>"+\
                                        "<option value='You aren&#39;t getting your verification code'>You aren't getting your verification code</option>"+\
                                        "</select>")
    reject_request.short_description = "Reject"
    
    def get_is_staff(self, obj):
        """
            Args:
                obj: model object
            Returns : True or False
        """
        return obj.is_staff

    get_is_staff.short_description = 'Admin'
    get_is_staff.boolean = True
    get_is_staff.admin_order_field = 'is_staff'

    def get_video_rights(self, obj):
        """
            Args:
                obj: Instance
            Returns: Returns True or False
        """
        if obj.id:
            p_obj = Profile.objects.get(user=obj.id)
            if p_obj.video_management_rights:
                return True
            else:
                if obj.is_superuser:
                    p_obj.video_management_rights = True
                    p_obj.save()
                    return True
                else:
                    return False

    get_video_rights.short_description = 'Video Management'
    get_video_rights.boolean = True
    get_video_rights.admin_order_field = 'profile__video_management_rights'

    def get_is_staff(self, obj):
        """
            Args:
                obj: Instance
            Returns: returns is staff or not (true or false)
        """
        return obj.is_staff

    get_is_staff.short_description = 'Admin'
    get_is_staff.boolean = True
    get_is_staff.admin_order_field = 'is_staff'

    def get_payment_rights(self, obj):
        """
            Args:
                obj: Instance
            Returns: True or False
        """
        if obj.id:
            p_obj = Profile.objects.get(user=obj.id)
            if p_obj.payment_management_rights:
                return True
            else:
                if obj.is_superuser:
                    p_obj.payment_management_rights = True
                    p_obj.save()
                    return True
                else:
                    return False

    get_payment_rights.short_description = 'Payment Management'
    get_payment_rights.boolean = True
    get_payment_rights.admin_order_field = 'profile__payment_management_rights'

    def get_copy_rights(self, obj):
        """
            Args:
                obj: Instance
            Returns: Returns True or False
        """
        if obj.id:
            p_obj = Profile.objects.get(user=obj.id)
            if p_obj.copyright_investigation_rights:
                return True
            else:
                if obj.is_superuser:
                    p_obj.copyright_investigation_rights = True
                    p_obj.save()
                    return True
                else:
                    return False

    get_copy_rights.short_description = 'Copyright Management'
    get_copy_rights.boolean = True
    get_copy_rights.admin_order_field = 'profile__copyright_investigation_rights'

    def get_bug_rights(self, obj):
        """
            Args:
                obj: Instance
            Returns: Returns True or False
        """
        if obj.id:
            p_obj = Profile.objects.get(user=obj.id)
            if p_obj.bug_rights:
                return True
            else:
                if obj.is_superuser:
                    p_obj.bug_rights = True
                    p_obj.save()
                    return True
                else:
                    return False

    get_bug_rights.short_description = 'Bug Management'
    get_bug_rights.boolean = True
    get_bug_rights.admin_order_field = 'profile__bug_rights'

    def get_inappropriate_rights(self, obj):
        """
            Args:
                obj: Instance
            Returns: Returns True or False
        """
        if obj.id:
            p_obj = Profile.objects.get(user=obj.id)
            if p_obj.inappropriate_rights:
                return True
            else:
                if obj.is_superuser:
                    p_obj.inappropriate_rights = True
                    p_obj.save()
                    return True
                else:
                    return False

    get_inappropriate_rights.short_description = 'Inappropriate Management'
    get_inappropriate_rights.boolean = True
    get_inappropriate_rights.admin_order_field = 'profile__inappropriate_rights'

    def assing_video_management(self, request, queryset):
        """
            Comment:  Video Management Add Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Video Management Rights of Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_add_skigit = Permission.objects.get(name='Can add Skigit')
                can_change_skigit = Permission.objects.get(name='Can change Skigit')
                if not obj.is_staff:
                    obj.is_staff = True

                    obj.user_permissions.add(can_add_skigit.id, can_change_skigit.id)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.video_management_rights:
                            p_obj.video_management_rights = True
                            obj.save()
                            p_obj.save()
                else:
                    obj.user_permissions.add(can_add_skigit.id, can_change_skigit.id)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.video_management_rights:
                            p_obj.video_management_rights = True
                            obj.save()
                            p_obj.save()

    assing_video_management.short_description = "Assign Video Management to selected Users"

    def remove_video_management(self, request, queryset):
        """
            Comment:  Video Management Remove Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Video Management Rights of Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_add_skigit = Permission.objects.get(name='Can add Skigit')
                can_change_skigit = Permission.objects.get(name='Can change Skigit')
                obj.user_permissions.remove(can_add_skigit.id, can_change_skigit.id)
                profile_obj = Profile.objects.filter(user=obj.id)
                for p_obj in profile_obj:
                    if p_obj.payment_management_rights:
                        obj.is_staff = True
                    elif p_obj.copyright_investigation_rights:
                        obj.is_staff = True
                    elif p_obj.bug_rights:
                        obj.is_staff = True
                    elif p_obj.inappropriate_rights:
                        obj.is_staff = True
                    else:
                        obj.is_staff = False
                    if p_obj.video_management_rights:
                        p_obj.video_management_rights = False
                        obj.save()
                        p_obj.save()

    remove_video_management.short_description = "Remove Video Management to selected Users"

    def assing_payment_management(self, request, queryset):
        """
            Comment:  Payment Management Add Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Payment Management Rights to Marked Users
        """
        can_add_payment = Permission.objects.get(name='Can add Payment')
        can_change_payment = Permission.objects.get(name='Can change Payment')
        for obj in queryset:
            if not obj.is_superuser:
                if not obj.is_staff:
                    obj.is_staff = True
                obj.user_permissions.add(can_add_payment.id, can_change_payment.id)
                profile_obj = Profile.objects.filter(user=obj.id)
                for p_obj in profile_obj:
                    if not p_obj.payment_management_rights:
                        p_obj.payment_management_rights = True
                        obj.save()
                        p_obj.save()

    assing_payment_management.short_description = "Assign Payment Management to selected Users"

    def remove_payment_management(self, request, queryset):
        """
            Comment:  Payment Management Remove Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Paymet Management Rights to Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_add_payment = Permission.objects.get(name='Can add Payment')
                can_change_payment = Permission.objects.get(name='Can change Payment')
                obj.user_permissions.remove(can_add_payment.id, can_change_payment.id)
                profile_obj = Profile.objects.filter(user=obj.id)
                obj.is_staff = False
                for p_obj in profile_obj:
                    if p_obj.video_management_rights:
                        obj.is_staff = True
                    elif p_obj.copyright_investigation_rights:
                        obj.is_staff = True
                    elif p_obj.bug_rights:
                        obj.is_staff = True
                    elif p_obj.inappropriate_rights:
                        obj.is_staff = True
                    else:
                        obj.is_staff = False
                    if p_obj.payment_management_rights:
                        p_obj.payment_management_rights = False
                        obj.save()
                        p_obj.save()

    remove_payment_management.short_description = "Remove Payment Management to selected Users"

    def assign_copyright_management(self, request, queryset):
        """
            Comment:  Copyright Management Add Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Copyright Management of Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_change_copyrightinfrigement = Permission.objects.get(name='Can change Copyright Infringement')
                can_change_copyrightinvestigation = Permission.objects.get(name='Can change Copyright Investigation')
                can_add_copyrightinvestigation = Permission.objects.get(name='Can add Copyright Investigation')
                if not obj.is_staff:
                    obj.is_staff = True

                    obj.user_permissions.add(can_change_copyrightinfrigement.id, can_change_copyrightinvestigation.id,
                                             can_add_copyrightinvestigation.id)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.copyright_investigation_rights:
                            p_obj.copyright_investigation_rights = True
                            obj.save()
                            p_obj.save()
                else:
                    obj.user_permissions.add(can_change_copyrightinvestigation.id, can_change_copyrightinfrigement.id,
                                             can_add_copyrightinvestigation.id)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.copyright_investigation_rights:
                            p_obj.copyright_investigation_rights = True
                            obj.save()
                            p_obj.save()

    assign_copyright_management.short_description = "Assign Copyright Management to selected Users"

    def remove_copyright_management(self, request, queryset):
        """
            Comment:  Copyright Management Remove Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Copyright Management to Marked Users
        """
        # inappropriate_rights
        for obj in queryset:
            if not obj.is_superuser:
                can_change_copyrightinfrigement = Permission.objects.get(name='Can change Copyright Infringement')
                can_change_copyrightinvestigation = Permission.objects.get(name='Can change Copyright Investigation')
                can_add_copyrightinvestigation = Permission.objects.get(name='Can add Copyright Investigation')
                obj.user_permissions.remove(can_change_copyrightinfrigement.id, can_change_copyrightinvestigation.id,
                                            can_add_copyrightinvestigation.id)
                profile_obj = Profile.objects.filter(user=obj.id)
                obj.is_staff = False
                for p_obj in profile_obj:
                    if p_obj.video_management_rights:
                        obj.is_staff = True
                    elif p_obj.payment_management_rights:
                        obj.is_staff = True
                    elif p_obj.bug_rights:
                        obj.is_staff = True
                    elif p_obj.inappropriate_rights:
                        obj.is_staff = True
                    else:
                        obj.is_staff = False
                    if p_obj.copyright_investigation_rights:
                        p_obj.copyright_investigation_rights = False
                        obj.save()
                        p_obj.save()

    remove_copyright_management.short_description = "Remove Copyright Management to selected Users"

    def assign_inappropriate_management(self, request, queryset):
        """
            Comment:  Copyright Management Add Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Copyright Management of Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_change_inappropriate = Permission.objects.get(name='Can change Inappropriate skigit')
                can_change_investigation = Permission.objects.get(name='Can change Inappropriate skigit Investigator')
                can_add_investigation = Permission.objects.get(name='Can add Inappropriate skigit Investigator')

                if not obj.is_staff:
                    obj.is_staff = True

                    obj.user_permissions.add(can_change_inappropriate, can_add_investigation,
                                             can_change_investigation)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.inappropriate_rights:
                            p_obj.inappropriate_rights = True
                            obj.save()
                            p_obj.save()
                else:
                    obj.user_permissions.add(can_change_inappropriate.id, can_change_investigation.id,
                                             can_add_investigation.id)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.inappropriate_rights:
                            p_obj.inappropriate_rights = True
                            obj.save()
                            p_obj.save()

    assign_inappropriate_management.short_description = "Assign Inappropriate Management to selected Users"

    def remove_inappropriate_management(self, request, queryset):
        """
            Comment:  Inappropriate Management Remove Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Inappropriate Management to Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_change_inappropriate = Permission.objects.get(name='Can change Inappropriate skigit')
                can_change_investigation = Permission.objects.get(name='Can change Inappropriate skigit Investigator')
                can_add_investigation = Permission.objects.get(name='Can add Inappropriate skigit Investigator')
                obj.user_permissions.remove(can_change_inappropriate, can_change_investigation,
                                            can_add_investigation)
                profile_obj = Profile.objects.filter(user=obj.id)
                obj.is_staff = False
                for p_obj in profile_obj:
                    if p_obj.video_management_rights:
                        obj.is_staff = True
                    elif p_obj.payment_management_rights:
                        obj.is_staff = True
                    elif p_obj.bug_rights:
                        obj.is_staff = True
                    elif p_obj.copyright_investigation_rights:
                        obj.is_staff = True
                    else:
                        obj.is_staff = False
                    if p_obj.inappropriate_rights:
                        p_obj.inappropriate_rights = False
                        obj.save()
                        p_obj.save()

    remove_inappropriate_management.short_description = "Remove Inappropriate Management to selected Users"

    def assign_bug_management(self, request, queryset):
        """
            Comment:  Bug Management Add Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Bug Management of Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_change_bug = Permission.objects.get(name='Can change Bug Report Management')
                if not obj.is_staff:
                    obj.is_staff = True

                    obj.user_permissions.add(can_change_bug.id)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.bug_rights:
                            p_obj.bug_rights = True
                            obj.save()
                            p_obj.save()
                else:
                    obj.user_permissions.add(can_change_bug.id)
                    profile_obj = Profile.objects.filter(user=obj.id)
                    for p_obj in profile_obj:
                        if not p_obj.bug_rights:
                            p_obj.bug_rights = True
                            obj.save()
                            p_obj.save()

    assign_bug_management.short_description = "Assign Bug Management to selected Users"

    def remove_Bug_management(self, request, queryset):
        """
            Comment:  Bug Management Remove Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Bug Management to Marked Users
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_change_bug = Permission.objects.get(name='Can change Bug Report Management')
                obj.user_permissions.remove(can_change_bug.id)
                profile_obj = Profile.objects.filter(user=obj.id)
                obj.is_staff = False
                for p_obj in profile_obj:
                    if p_obj.video_management_rights:
                        obj.is_staff = True
                    elif p_obj.payment_management_rights:
                        obj.is_staff = True
                    elif p_obj.copyright_investigation_rights:
                        obj.is_staff = True
                    else:
                        obj.is_staff = False
                    if p_obj.bug_rights:
                        p_obj.bug_rights = False
                        obj.save()
                        p_obj.save()

    remove_Bug_management.short_description = "Remove Bug Management to selected Users"

    def add_all_rights(self, request, queryset):
        """
            Comment:  Add All Management Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Add All Management Permissions
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_change_inappropriate = Permission.objects.get(name='Can change Inappropriate skigit')
                can_change_investigation = Permission.objects.get(name='Can change Inappropriate skigit Investigator')
                can_add_investigation = Permission.objects.get(name='Can add Inappropriate skigit Investigator')
                can_change_bug = Permission.objects.get(name='Can change Bug Report Management')
                can_add_skigit = Permission.objects.get(name='Can add Skigit')
                can_change_skigit = Permission.objects.get(name='Can change Skigit')
                can_add_payment = Permission.objects.get(name='Can add Payment')
                can_change_payment = Permission.objects.get(name='Can change Payment')
                can_change_copyrightinfrigement = Permission.objects.get(name='Can change Copyright Infringement')
                can_change_copyrightinvestigation = Permission.objects.get(name='Can change Copyright Investigation')
                can_add_copyrightinvestigation = Permission.objects.get(name='Can add Copyright Investigation')
                obj.user_permissions.add(can_change_copyrightinfrigement.id, can_change_copyrightinvestigation.id,
                                         can_add_skigit.id, can_change_skigit.id, can_add_payment.id,
                                         can_change_payment.id, can_add_copyrightinvestigation.id, can_change_bug.id,
                                         can_change_inappropriate.id, can_change_investigation.id,
                                         can_add_investigation.id)
                profile_obj = Profile.objects.filter(user=obj.id)
                obj.is_staff = True
                for p_obj in profile_obj:
                    p_obj.copyright_investigation_rights = True
                    p_obj.payment_management_rights = True
                    p_obj.video_management_rights = True
                    p_obj.bug_rights = True
                    p_obj.inappropriate_rights = True
                    obj.save()
                    p_obj.save()

    add_all_rights.short_description = "Add All Management Rights to selected Users"

    def remove_all_rights(self, request, queryset):
        """
            Comment:  Remove All Management Permissions
            Args:
                request: Requested user
                queryset: obj
            Returns: Remove All Management Permissions
        """

        for obj in queryset:
            if not obj.is_superuser:
                can_change_bug = Permission.objects.get(name='Can change Bug Report Management')
                can_add_skigit = Permission.objects.get(name='Can add Skigit')
                can_change_skigit = Permission.objects.get(name='Can change Skigit')
                can_add_payment = Permission.objects.get(name='Can add Payment')
                can_change_payment = Permission.objects.get(name='Can change Payment')
                can_change_copyrightinfrigement = Permission.objects.get(name='Can change Copyright Infringement')
                can_change_copyrightinvestigation = Permission.objects.get(name='Can change Copyright Investigation')
                can_add_copyrightinvestigation = Permission.objects.get(name='Can add Copyright Investigation')
                can_change_inappropriate = Permission.objects.get(name='Can change Inappropriate skigit')
                can_change_investigation = Permission.objects.get(name='Can change Inappropriate skigit Investigator')
                can_add_investigation = Permission.objects.get(name='Can add Inappropriate skigit Investigator')
                obj.user_permissions.remove(can_change_copyrightinfrigement, can_change_copyrightinvestigation,
                                            can_add_skigit, can_change_skigit, can_add_payment,
                                            can_change_payment, can_add_copyrightinvestigation, can_change_bug,
                                            can_change_inappropriate, can_change_investigation,
                                            can_add_investigation)
                profile_obj = Profile.objects.filter(user=obj.id)
                obj.is_staff = False
                for p_obj in profile_obj:
                    p_obj.copyright_investigation_rights = False
                    p_obj.payment_management_rights = False
                    p_obj.video_management_rights = False
                    p_obj.bug_rights = False
                    p_obj.inappropriate_rights = False
                    obj.save()
                    p_obj.save()

    remove_all_rights.short_description = "Remove All Management Rights to selected Users"


admin.site.register(User, UserProfileAdmin)


class PaymentAdmin(admin.ModelAdmin):
    """
        PAYMENT ADMIN
    """
    list_display = ('payment_email', 'payment_name')


admin.site.register(Payment, PaymentAdmin)


class InappropriateSkigitReasonAdmin(admin.ModelAdmin):
    """
        Inappropriate Skigit
    """
    model = InappropriateSkigitReason
    actions = ['delete_selected', ]
    list_display = ('reason_title', 'created_date')
    list_filter = ('created_date',)
    search_fields = ['reason_title', ]
    prepopulated_fields = {'reason_slug': ('reason_title',)}


# def appropriate_skigit(modeladmin, request, queryset):
#     """
#         Args:
#             modeladmin:
#             request:
#             queryset:
#             Status = ("1", 'Open'), ("2", 'Under Investigation'), ("3", 'Closed'), ("4", 'Remove Skigit'),
#     """
#     for obj in queryset:
#         if not obj.action:
#             obj.action = '1'
#             obj.save()
#             # obj.skigit.
#             # message = "Dear %s to notify that %s is approved by Skigit team is not %s " % (obj.reported_user.username,
#             #                                                                                obj.skigit.skigit_id.title,
#             #                                                                                obj.reason.reason_title)
#             # subject = "Inappropriate | Skigit"
#             # send_mail(subject, message, settings.EMAIL_HOST_USER, [obj.reported_user.email, ])
#             temp_action = None
#             temp_status = None
#             row = InappropriateSkigit.objects.filter(skigit=obj.skigit).first()
#
#             if row.action is not False and not row.action:
#                 temp_action = True
#                 temp_status = False
#
#             video = VideoDetail.objects.get(pk=obj.skigit.id)
#             video.inappropriate_skigit = temp_action
#             video.status = 1
#             video.save()
#
#             # change status in inapp table
#             inapp = InappropriateSkigit.objects.filter(skigit=obj.skigit).first()
#             inapp.status = "3"
#             inapp.save()
# appropriate_skigit.short_description = "Mark selected Skigit as Appropriate"
#
#
# def inappropriate_skigit(modeladmin, request, queryset):
#     """
#         Args:
#             modeladmin:
#             request:
#             queryset:
#     """
#     for obj in queryset:
#         if not obj.action:
#             obj.action = False
#             obj.save()
#             message = "<p>Dear %s to notify  %s is %s and removed by Skigit team</p> " % (obj.reported_user.username,
#                                                                                           obj.skigit.skigit_id.title,
#                                                                                           obj.reason.reason_title)
#             subject = "Inappropriate | Skigit"
#             send_mail(subject, message, settings.EMAIL_HOST_USER, [obj.reported_user.email, ])
#             message = "Dear %s to notify that your uploaded Skigit %s is removed by due to the %s reason by Skigit team"\
#                       % (obj.skigit.skigit_id.user.username, obj.skigit.skigit_id.title, obj.reason.reason_title)
#             subject = "Inappropriate | Skigit"
#             send_mail(subject, message, settings.EMAIL_HOST_USER, [obj.skigit.skigit_id.user.email, ])
#             temp_action = True
#             temp_status = False
#
#             # mark status in inapp table
#             inapp = InappropriateSkigit.objects.get(skigit=obj.skigit)
#             inapp.status = 3
#             inapp.save()
#         else:
#             obj.action = False
#             obj.save()
#             temp_action = True
#             temp_status = False
#
#         video = VideoDetail.objects.get(pk=obj.skigit.id)
#         video.inappropriate_skigit = temp_action
#         video.status = temp_status
#         video.save()
#
#         # main_video = Video.objects.get(pk=video.skigit_id)
#         # main_video.delete()
# inappropriate_skigit.short_description = "Mark selected Skigit as Inappropriate"


class MyModelForm(forms.ModelForm):
    """
        My Model Form
    """

    MY_CHOICES = (
        ('A', 'Choice A'),
        ('B', 'Choice B'),
    )
    stuff = forms.ChoiceField(choices=MY_CHOICES)


class InappropriateInvestigatorForm(forms.ModelForm):
    """
        Inappropriate Investigator Admin Form
    """

    def __init__(self, *args, **kwargs):
        super(InappropriateInvestigatorForm, self).__init__(*args, **kwargs)
        self.fields['result_remove_all'].choices = self.fields['result_remove_all'].choices[1:]
        self.fields['result_strike'].choices = self.fields['result_strike'].choices[1:]


class InappropriateInvestigatorInline(admin.StackedInline):
    """
        Investigator Admin Inline
    """
    form = InappropriateInvestigatorForm
    readonly_fields = ['get_investigator_name']
    fieldsets = (
        (
            None,
            {
                'fields': ('get_investigator_name', 'result_remove_all', 'result_strike', 'investigation_discription',
                           'action_taken')
            }
        ),
    )

    radio_fields = {'result_remove_all': admin.HORIZONTAL, 'result_strike': admin.HORIZONTAL}
    model = InappropriateSkigitInvestigator
    max_num = 1

    def get_investigator_name(self, obj):
        """
            Get Investigator Name
        """
        if obj.investigating_user:
            if obj.investigating_user.get_full_name():
                return obj.investigating_user.get_full_name()
            else:
                return obj.investigating_user.username
        else:
            return ''

    get_investigator_name.allow_tags = True
    get_investigator_name.short_description = 'Investigator Name'

    def has_delete_permission(self, request, obj=None):
        return False


class InappropriateSkigitAdmin(admin.ModelAdmin):
    """
        Inappropriate Model Admin
    """
    inlines = [InappropriateInvestigatorInline]

    list_display = ('get_invastigation_id', 'get_skigit_id', 'get_primary_skigit', 'status', 'get_inapp_action',
                    'related_skigit_title', 'related_skigit_category',
                    'related_skigit_create_user', 'get_strikes', 'get_submitter_name',
                    'related_inappropriate_reason', 'related_swf', 'created_date')
    readonly_fields = ['get_invastigation_id', 'get_user_name', 'get_submitter_email', 'get_video_creator_user_name',
                       'get_video_creator_email', 'get_skigit', 'reported_user', 'action', 'reason',
                       'get_submitter_email']
    fields = ['get_invastigation_id', 'get_user_name', 'get_submitter_email', 'get_video_creator_user_name',
              'get_video_creator_email', 'get_skigit', 'reason', 'status', 'action']
    fk_name = ('skigit', 'reported_user', 'reason')
    actions = ['delete_selected', ]
    list_filter = ('skigit__category', 'reason', 'status', 'action', 'created_date')

    search_fields = ['skigit__skigit_id__title', 'id', 'skigit__skigit_id__user__username',
                     'skigit__skigit_id__user__first_name', 'skigit__category__cat_name', 'skigit__made_by__username',
                     'skigit__made_by__first_name', 'reason__reason_title']

    list_per_page = 15

    class Media:
        js = (
            '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',  # jquery
            '/static/js/admin_js.js',  # app static folder
        )

    def get_primary_skigit(self, obj):
        if obj.skigit.plugged_skigit:
            return obj.skigit.plugged_skigit.title

    get_primary_skigit.allow_tags = True
    get_primary_skigit.short_description = 'Primary Skigit'
    get_primary_skigit.admin_order_field = 'skigit_id'

    def get_skigit_id(self, obj):
        return obj.skigit_id

    get_skigit_id.allow_tags = True
    get_skigit_id.short_description = 'ID'
    get_skigit_id.admin_order_field = 'skigit_id'

    def get_strikes(self, obj):
        if obj:
            strike_count = 0
            user_id = obj.skigit.skigit_id.user.id
            inappropriate_skigits = InappropriateSkigit.objects.filter(skigit__skigit_id__user__id=user_id)
            for inappro_skigit in inappropriate_skigits:
                if InappropriateSkigitInvestigator.objects.filter(id=inappro_skigit.id).exists():
                    investigator = InappropriateSkigitInvestigator.objects.get(id=inappro_skigit.id)
                    if investigator.get_result_strike_display() == 'Yes':
                        strike_count += 1
            return strike_count

    get_strikes.allow_tags = True
    get_strikes.short_description = 'Strikes'

    def get_inapp_action(self, obj):
        if obj.action == '0':
            return format_html('<span style="color:orange;">Pending</span>')
        elif obj.action == '1':
            return format_html('<span style="color:green;">Appropriate</span>')
        elif obj.action == '2':
            return format_html('<span style="color:red;">Inappropriate</span>')

    get_inapp_action.allow_tags = True
    get_inapp_action.short_description = 'Action'
    get_inapp_action.admin_order_field = 'action'

    def get_invastigation_id(self, obj):
        if obj.id:
            return format_html('<span>%010d</span>' % obj.id)

    get_invastigation_id.allow_tags = True
    get_invastigation_id.short_description = 'Investigation Id'
    get_invastigation_id.admin_order_field = 'id'

    def get_submitter_email(self, obj):
        if obj.reported_user:
            return format_html('<a href="mailto:{0}">{0}</a>'.format(obj.reported_user.email))

    get_submitter_email.allow_tags = True
    get_submitter_email.short_description = 'Submitter  Email'
    get_submitter_email.admin_order_field = 'reported_user__user__email'

    def inappropriate_skigit_id(self, obj):
        return obj.id

    inappropriate_skigit_id.short_description = 'Inappropriate Skigit ID'

    def comaplaint_date(self, obj):
        return obj.created_date

    comaplaint_date.short_description = 'Complaint Date'

    def related_skigit_id(self, obj):
        return obj.skigit.id

    related_skigit_id.short_description = 'Skigit Id'

    def related_skigit_title(self, obj):
        return obj.skigit.title

    related_skigit_title.short_description = 'Skigit Title'

    def related_skigit_category(self, obj):
        return obj.skigit.category.cat_name

    related_skigit_category.short_description = 'Category'

    def related_reported_user_title(self, obj):
        return obj.reported_user.username

    related_reported_user_title.short_description = 'Submitted By'

    def related_reported_user_email(self, obj):
        return obj.reported_user.email

    related_reported_user_email.short_description = 'Submitter Email'

    def related_skigit_create_user(self, obj):
        return obj.skigit.skigit_id.user.username

    related_skigit_create_user.short_description = 'Skigit Creator'

    def get_submitter_name(self, obj):
        return obj.reported_user.username

    get_submitter_name.short_description = 'Submitter Name'

    def related_inappropriate_reason(self, obj):
        return obj.reason.reason_title

    related_inappropriate_reason.short_description = 'Inappropriate Reason'

    def related_swf(self, obj):
        return format_html('<a href="%s">Show</a>' % (obj.skigit.skigit_id.get_absolute_url()))

    related_swf.allow_tags = True
    related_swf.short_description = 'Video Link'

    def select1(self, obj):
        return format_html('<input inappid="%s"  id="update_button" name="update_button" type="button" value="Update"/>' % obj.id)

    select1.allow_tags = True
    select1.short_description = 'Action'

    def get_user_name(self, obj):
        if obj.reported_user:
            return obj.reported_user.username
        else:
            return ''

    get_user_name.allow_tags = True
    get_user_name.short_description = 'Submitter User Name'
    get_user_name.admin_order_field = 'bug_page_url'

    def get_video_creator_user_name(self, obj):
        return obj.skigit.skigit_id.user.username

    get_video_creator_user_name.allow_tags = True
    get_video_creator_user_name.short_description = 'Creator User Name'
    get_video_creator_user_name.admin_order_field = 'bug_page_url'

    def get_video_creator_email(self, obj):
        return obj.skigit.skigit_id.user.email

    get_video_creator_email.allow_tags = True
    get_video_creator_email.short_description = 'Creator Email'
    get_video_creator_email.admin_order_field = 'bug_page_url'

    def get_skigit(self, obj):
        if obj.skigit:
            return "Skigit ID: <a href='%s%s' target='_blank'>%s</a>," \
                   " Skigit Title: <a href='%s%s' target='_blank'>%s</a>" \
                   % (settings.HOST,
                      reverse('skigit_data', kwargs={'pk': obj.skigit.id}),
                      obj.skigit.id,
                      settings.HOST,
                      reverse('skigit_data', kwargs={'pk': obj.skigit.id}),
                      obj.skigit.title)

    get_skigit.allow_tags = True
    get_skigit.short_description = 'Inappropriate work on Skigit'
    get_skigit.admin_order_field = 'skigit__skigit_id'

    def save_formset(self, request, form, formset, change):

        investigator = formset.save(commit=False)
        inappropriate = form.save(commit=False)
        inapp_status = InappropriateSkigit.objects.get(id=inappropriate.id).status
        result_remove_all = InappropriateSkigitInvestigator.objects.get(inapp_skigit=inappropriate.id).result_remove_all
        result_strike = InappropriateSkigitInvestigator.objects.get(inapp_skigit=inappropriate.id).result_strike
        for instance in investigator:
            instance.investigating_user = request.user
            instance.save()
        formset.save_m2m()
        if (inappropriate.status == '2'):
            inappropriate.status = '2'
            inappropriate.action = '0'
            if VideoDetail.objects.filter(id=inappropriate.skigit.id).exists():
                VideoDetail.objects.filter(id=inappropriate.skigit.id).update(
                    status=1, inappropriate_skigit='0',
                    published_at=timezone.now(), deleted_at=None
                )
        elif (inappropriate.status == '1'):
            inappropriate.status = '1'
            inappropriate.action = '0'
        elif inappropriate.status == '3':
            InappropriateSkigitInvestigator.objects.filter(inapp_skigit=inappropriate.id).update(
                result_remove_all=False)
            inappropriate.action = '1'
            if VideoDetail.objects.filter(id=inappropriate.skigit.id).exists():
                VideoDetail.objects.filter(id=inappropriate.skigit.id).update(
                    status=1, inappropriate_skigit='1',
                    published_at=timezone.now(), deleted_at=None
                )
                vid_title = VideoDetail.objects.get(id=inappropriate.skigit.id).title
                investigation_id = '%010d' % inappropriate.id

                EmailTemplate.send(
                    template_key="inappropriate_acceptance",
                    emails=inappropriate.reported_user.email,
                    context={
                        "investigation_id": investigation_id,
                        "skigit_id": inappropriate.skigit.id,
                        "title": vid_title,
                        "host": ''.join(settings.HOST)
                    }
                )
        elif inappropriate.status == '4':
            InappropriateSkigitInvestigator.objects.filter(inapp_skigit=inappropriate.id).update(result_remove_all=True)
            inappropriate.action = '2'
            if VideoDetail.objects.filter(id=inappropriate.skigit.id).exists():
                VideoDetail.objects.filter(id=inappropriate.skigit.id).update(
                    status=2, inappropriate_skigit='2',
                    deleted_at=timezone.now(), published_at=None
                )
                vid_title = VideoDetail.objects.get(id=inappropriate.skigit.id).title
                investigation_id = '%010d' % inappropriate.id

                EmailTemplate.send(
                    template_key="your_skigit_is_inappropriate",
                    emails=inappropriate.skigit.skigit_id.user.email,
                    context={
                        "title": vid_title,
                        "id": inappropriate.skigit.id,
                        "host": ''.join(settings.HOST)
                    }
                )

                EmailTemplate.send(
                    template_key="inappropriate_rejection",
                    emails=inappropriate.reported_user.email,
                    context={
                        "investigation_id": investigation_id,
                        "skigit_id": inappropriate.skigit.id,
                        "title": vid_title,
                        "host": ''.join(settings.HOST)
                    }
                )

        inappropriate.save()

    def save_model(self, request, obj, form, change):
        if InappropriateSkigitInvestigator.objects.filter(inapp_skigit=obj.id).exists():
            InappropriateSkigitInvestigator.objects.filter(
                inapp_skigit=obj.id).update(investigating_user=request.user)


# Admin Bug Management
class AdminBugReportManagement(admin.ModelAdmin):
    readonly_fields = ['get_bug_id', 'user', 'skigit_id', 'get_skigit_id', 'bug_title', 'get_bug_page_url',
                       'get_created_date', 'get_bug_repeted', 'bug_description', 'get_updated_date']
    fields = ['get_bug_id', 'bug_title', 'user', 'get_skigit_id', 'skigit_id', 'get_bug_page_url', 'get_bug_repeted',
              'bug_description', 'get_created_date', 'bug_comment', 'bug_status', 'get_updated_date', ]
    list_display = ['get_bug_id', 'bug_title', 'get_bug_page_url', 'bug_status', 'bug_repeated', 'get_created_date']
    actions = ['delete_selected', ]
    list_filter = ('bug_status', 'bug_repeated')
    search_fields = ['bug_title', 'id', 'bug_description', 'bug_status', 'bug_repeated']
    list_per_page = 20

    def get_created_date(self, obj):
        if obj.created_date:
            return obj.created_date.strftime("%d %b %Y")
        return ''

    get_created_date.allow_tags = True
    get_created_date.admin_order_field = 'created_date'
    get_created_date.short_description = 'Date Reported'

    def get_updated_date(self, obj):
        if obj.updated_date:
            return obj.updated_date.strftime("%d %b %Y")
        return ''

    get_updated_date.allow_tags = True
    get_updated_date.admin_order_field = 'updated_date'
    get_updated_date.short_description = 'Date submitted to maintenance'

    def get_bug_repeted(self, obj):
        if obj.bug_repeated:
            if obj.bug_repeated is True:
                return 'Yes'
            else:
                return 'No'
        return 'No'

    get_bug_repeted.allow_tags = True
    get_bug_repeted.short_description = 'Bug repeated'
    get_bug_repeted.admin_order_field = 'bug_repeated'

    def get_bug_id(self, obj):
        """
            Args:
                obj: Instance
            Returns: Url Of Youtube Video List Page
        """
        return format_html('<span>%010d</span>' % obj.id)

    get_bug_id.allow_tags = True
    get_bug_id.short_description = 'Bug ID'
    get_bug_id.admin_order_field = 'id'

    def get_skigit_id(self, obj):
        if obj.skigit_id:
            return obj.skigit_id.id
        return ''

    get_skigit_id.allow_tags = True
    get_skigit_id.short_description = 'Skigit ID'
    get_skigit_id.admin_order_field = 'skigit_id__id'

    def get_bug_page_url(self, obj):
        """
            Args:
                obj: Instance
            Returns: Url Of Youtube Video List Page
        """
        return format_html('<a href="{0}" target="_blank">{0}</a>'.format(obj.bug_page_url))

    get_bug_page_url.allow_tags = True
    get_bug_page_url.short_description = 'URL'
    get_bug_page_url.admin_order_field = 'bug_page_url'

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        else:
            return False


admin.site.register(BugReport, AdminBugReportManagement)


class InvestigatorAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(InvestigatorAdminForm, self).__init__(*args, **kwargs)
        self.fields['remove_all'].choices = self.fields['remove_all'].choices[1:]
        self.fields['strike'].choices = self.fields['strike'].choices[1:]
        # self.fields['investigator_name'].queryset = Profile.objects.filter(copyright_investigation_rights=True)


class AdminInvestigatorInLine(admin.StackedInline):
    form = InvestigatorAdminForm
    readonly_fields = ['get_investigator_name']
    fieldsets = (
        (
            None,
            {
                'fields': ('get_investigator_name', 'remove_all', 'strike', 'description', 'action')
            }
        ),
    )

    radio_fields = {'remove_all': admin.HORIZONTAL, 'strike': admin.HORIZONTAL}
    model = CopyRightInvestigation
    max_num = 1

    def get_investigator_name(self, obj):
        if obj.investigator_name:
            if obj.investigator_name.user.get_full_name():
                return obj.investigator_name.user.get_full_name()
            else:
                return obj.investigator_name.user.username
        else:
            return ''

    get_investigator_name.allow_tags = True
    get_investigator_name.short_description = 'Investigator Name'

    def has_delete_permission(self, request, obj=None):
        return False


class AdminCopyRightInfringement(admin.ModelAdmin):
    inlines = [AdminInvestigatorInLine]
    readonly_fields = ['get_copy_right_id', 'user_id', 'get_my_work_on_url', 'description',
                       'get_skigit_for_investigation', 'address', 'city', 'state', 'zip_code', 'country',
                       'phone', 'email', 'submitter_request', 'full_name', 'complaint_date']
    fields = ['get_copy_right_id', 'full_name', 'get_my_work_on_url', 'description', 'get_skigit_for_investigation',
              'address', 'city', 'state', 'zip_code', 'country', 'phone', 'email', 'submitter_request', 'user_id',
              'complaint_date', 'status']
    list_display = ['get_copy_right_id', 'get_skigit_id', 'get_skigit_title', 'get_primary_skigit', 'user_id', 'get_investigation_status',
                    'get_my_work_on_url', 'phone', 'email', 'complaint_date']
    search_fields = ['id', 'complaint_date', 'email', 'phone']
    list_filter = ['status', ]
    list_per_page = 20

    def get_skigit_id(self, obj):
        return obj.skigit_id

    get_skigit_id.allow_tags = True
    get_skigit_id.short_description = 'ID'
    get_skigit_id.admin_order_field = 'skigit_id'

    def get_skigit_title(self, obj):
        video_detail = VideoDetail.objects.filter(id=obj.skigit_id)
        if video_detail.exists():
            return video_detail[0].title


    get_skigit_title.allow_tags = True
    get_skigit_title.short_description = 'Skigit Title'
    get_skigit_title.admin_order_field = 'skigit_id'

    def get_my_work_on_url(self, obj):
        """
            Original work URL by Copyrigte complaint registered user
        """
        return format_html('<a href="{0}" target="_blank">{0}</a>'.format(obj.urls))

    get_my_work_on_url.allow_tags = True
    get_my_work_on_url.short_description = 'User Identified work'
    get_my_work_on_url.admin_order_field = 'urls'

    def get_copy_right_id(self, obj):
        """
            Args:
                obj: Instance
            Returns: Url Of Youtube Video List Page
        """
        return format_html('<span>%010d</span>' % obj.id)

    get_copy_right_id.allow_tags = True
    get_copy_right_id.short_description = 'Investigation Id'
    get_copy_right_id.admin_order_field = 'id'

    def get_skigit_for_investigation(self, obj):
        """
            Infringement Work on Skigit Name and ID
        """
        if obj.skigit_id:
            if VideoDetail.objects.filter(id=obj.skigit_id).exists():
                skigitt = VideoDetail.objects.get(id=obj.skigit_id)
                return "Skigit ID: <a href='{}{}' target='_blank'>{}</a>, " \
                       "Skigit Title: <a href='{}{}' target='_blank'>{}</a>".format(
                        settings.HOST,
                        reverse('skigit_data', kwargs={'pk': obj.skigit_id}),
                        obj.skigit_id,
                        settings.HOST,
                        reverse('skigit_data', kwargs={'pk': obj.skigit_id}),
                        skigitt.title)
            else:
                return "Skigit ID: <a href='%s%s' target='_blank'>%s</a>" % \
                       (settings.HOST,
                        reverse('skigit_data', kwargs={'pk': obj.skigit_id}),
                        obj.skigit_id)
        else:
            return ''

    get_skigit_for_investigation.allow_tags = True
    get_skigit_for_investigation.short_description = 'Infringed work on Skigit'
    get_skigit_for_investigation.admin_order_field = 'skigit_id'

    def get_primary_skigit(self, obj):
        if obj.skigit_id:
            if VideoDetail.objects.filter(id=obj.skigit_id).exists():
                skigitt = VideoDetail.objects.get(id=obj.skigit_id)
                if skigitt.plugged_skigit:
                    return skigitt.plugged_skigit.title
                else:
                    return skigitt.title

    get_primary_skigit.allow_tags = True
    get_primary_skigit.short_description = 'Primary Skigit'
    get_primary_skigit.admin_order_field = 'skigit_id'

    def get_investigation_status(self, obj):
        if obj.status:
            if obj.status == 0:
                return "Open"
            elif obj.status == 1:
                return "Under Investigation"
            elif obj.status == 2:
                return "Closed"
            elif obj.status == 3:
                return "Remove Skigit"
            else:
                return "Open"
        else:
            return 'Open'

    get_investigation_status.allow_tags = True
    get_investigation_status.short_description = 'Status'
    get_investigation_status.admin_order_field = 'status'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    def save_formset(self, request, form, formset, change):
        for f in formset:
            investigator = f.save(commit=False)
            break
        formset.save(commit=False)
        copy_right_content = form.save(commit=False)
        copy_status = copy_right_content.status
        result_remove_all = investigator.remove_all
        result_strike = investigator.strike
        profile_user = Profile.objects.get(user=request.user.id)
        investigator.investigator_name = profile_user
        investigator.save()
        if copy_right_content.status == 0 and (not result_remove_all or not result_strike):
            copy_right_content.status = 0
            if VideoDetail.objects.filter(id=copy_right_content.skigit_id).exists():
                VideoDetail.objects.filter(id=copy_right_content.skigit_id).update(
                    status=1, copyright_skigit='0',
                    published_at=timezone.now(), deleted_at=None
                )
        elif copy_right_content.status == 1 and (not result_remove_all or not result_strike):
            copy_right_content.status = 1
            if VideoDetail.objects.filter(id=copy_right_content.skigit_id).exists():
                VideoDetail.objects.filter(id=copy_right_content.skigit_id).update(
                    status=1, copyright_skigit='1',
                    published_at=timezone.now(), deleted_at=None
                )
        elif copy_right_content.status == 2 and (not result_remove_all or not result_strike):
            CopyRightInvestigation.objects.filter(copy_right=copy_right_content.id).update(remove_all=False)
            if VideoDetail.objects.filter(id=copy_right_content.skigit_id).exists():
                VideoDetail.objects.filter(id=copy_right_content.skigit_id).update(
                    status=1, copyright_skigit='2',
                    published_at=timezone.now(), deleted_at=None
                )
                if VideoDetail.objects.filter(id=copy_right_content.skigit_id).exists():
                    skigitt = VideoDetail.objects.get(id=copy_right_content.skigit_id)
                    investigation_id = '%010d' % copy_right_content.id

                    [EmailTemplate.send(
                        template_key="copyright_acceptance",
                        emails=receiver,
                        context={
                            "investigation_id": investigation_id,
                            "skigit_id": copy_right_content.skigit_id,
                            "title": skigitt.title,
                            "host": ''.join(settings.HOST)
                        }) for receiver in [copy_right_content.user_id.email, copy_right_content.email]]


        elif copy_right_content.status == 3:
            CopyRightInvestigation.objects.filter(copy_right=copy_right_content.id).update(remove_all=True)
            if VideoDetail.objects.filter(id=copy_right_content.skigit_id).exists():
                VideoDetail.objects.filter(id=copy_right_content.skigit_id).update(
                    status=2, copyright_skigit='3',
                    deleted_at=timezone.now(), published_at=None
                )
                vidTitle = VideoDetail.objects.get(id=copy_right_content.skigit_id).title
                vidUser = VideoDetail.objects.get(id=copy_right_content.skigit_id)
                investigation_id = '%010d' % copy_right_content.id

                EmailTemplate.send(
                    template_key="skigit_copyright_violation",
                    #emails=vidUser.made_by.email,
                    emails=vidUser.skigit_id.user.email,
                    context={
                        "skigit_id": copy_right_content.skigit_id,
                        "title": vidTitle,
                        "host": ''.join(settings.HOST)
                    })

                EmailTemplate.send(
                    template_key="copyright_rejection",
                    emails=copy_right_content.email,
                    context={
                        "investigation_id": investigation_id,
                        "skigit_id": copy_right_content.skigit_id,
                        "title": vidTitle,
                        "host": ''.join(settings.HOST)
                    })
        copy_right_content.save()


admin.site.register(CopyRightInfringement, AdminCopyRightInfringement)
VideoAdmin.actions_on_bottom = False
VideoAdmin.actions_on_top = True
admin.site.register(Video, VideoAdmin)
VideoDetailAdmin.actions_on_bottom = True
VideoDetailAdmin.actions_on_top = True
admin.site.register(VideoDetail, VideoDetailAdmin)
InappropriateSkigitAdmin.actions_on_bottom = False
InappropriateSkigitAdmin.actions_on_top = True
admin.site.register(InappropriateSkigit, InappropriateSkigitAdmin)
admin.site.register(Category, CategoryInline)
admin.site.register(SubjectCategory, SubjectCategoryInline)
InappropriateSkigitReasonAdmin.actions_on_bottom = False
InappropriateSkigitReasonAdmin.actions_on_top = True
admin.site.register(InappropriateSkigitReason, InappropriateSkigitReasonAdmin)
admin.site.register(Donation)
admin.site.register(Incentive, IncentiveAdmin)
