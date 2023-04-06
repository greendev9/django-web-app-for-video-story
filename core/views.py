import random
from heapq import merge
from itertools import chain
from user.models import Profile, BusinessLogo
import logging
import re
import json
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, render
from django.template.context import RequestContext
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView, View
from django.views.generic.base import RedirectView
from django.urls import reverse
from django.urls import get_resolver
from el_pagination.decorators import page_template
from social.models import Share
from sorl.thumbnail import get_thumbnail
from meta.views import Meta
from rest_framework import generics, views
from rest_framework.response import Response
from constance import config
from constance import settings as constance_settings

from core.utils import (is_user_general, get_all_logged_in_users, get_video_share_url, check_valid_url, is_verified_business_user, CustomIsAuthenticated,
                        generateOTP,verifyOTP,sendTwilioSMS,checkPhoneValidity)
                        
from friends.models import Friend
from invoices.models import Invoice
from skigit.models import Like, VideoDetail
from core.models import Category, SubjectCategory, GeneralSiteData
from core.serializers import CategorySerializer, SubjectCategorySerializer, UrlSerializer
from user.serializers import api_request_images
from mailpost.models import EmailTemplate

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('Core')

# for tests to solve truncate image issue
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_share_list(user, video):
    """

    :param user:
    :param video:
    :return: Get user share videos!
    """
    sharObj = Share.objects.filter(skigit_id=video, is_active=True, user=user.id).\
                order_by('to_user', '-pk').distinct('to_user')
    return [{'share_date': sh.created_date, 'username': sh.to_user.username if sh.to_user else -1, 'vid': sh.skigit_id_id}
            for sh in sharObj]


def get_friends_list(user):
    friend_list = []
    f_list = Friend.objects.filter(Q(to_user=user.id) | Q(from_user=user.id), status=1)
    if f_list.exists():
        from_user_list = f_list.exclude(from_user=user.id).values_list('from_user', flat=True).distinct()
        to_user_list = f_list.exclude(to_user=user.id).values_list('to_user', flat=True).distinct()
        fr_list = list(merge(from_user_list, to_user_list))
        friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')

        for friends in friends_detail:
            if friends.profile_img:
                l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
            else:
                l_img = "{0}{1}".format(settings.STATIC_URL,'images/noimage_user.jpg')
            friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                'name': friends.user.get_full_name(), 'image': l_img})
    return friend_list


# @method_decorator(ensure_csrf_cookie, name="dispatch")
class SkigitBaseView(TemplateView):

    description = "You gotta check out Skigit! Live, Share...Make the Difference!"

    def get_context_data(self, **kwargs):
        host = ''.join(settings.HOST)[:-1]
        og_image = None
        og_title = 'Skigit'
        og_description = self.description
        og_url = '{}{}'.format(host, reverse('index'))
        image_width = 600
        image_height = 500
        og_type = 'website'

        if 'skigit_id' in kwargs:
            skigit = VideoDetail.objects.filter(id=kwargs['skigit_id'])
            if skigit.exists():
                skigit = skigit[0]
                u_profile = skigit.skigit_id.user.profile
                if u_profile.profile_img:
                  company_logo_url = api_request_images(u_profile.profile_img, quality=99, format='PNG')
                else:
                  company_logo_url = 'images/noimage_user.jpg'
                try:
                    og_image = get_video_share_url(self.request, skigit, company_logo_url)
                    image_width = 600
                    image_height = 600
                except Exception as exc:
                    logger.error("The skigit share image throws error:", exc)

                og_url = '{}{}'.format(host, reverse('skigit_data', kwargs={'pk': skigit.id}))
                og_description = skigit.why_rocks
                og_title = skigit.title
        og_image = settings.MEDIA_HOST_URL + og_image if og_image else "{0}{1}?date=last".format(settings.STATIC_HOST_URL, 'images/logo_social.png')
        meta = Meta(
            title=og_title,
            description=og_description,
            image=og_image,
            image_width=image_width,
            image_height=image_height,
            url=og_url,
            use_og=True,
            object_type=og_type,
            use_facebook=True,
            use_twitter=True,
            facebook_app_id= settings.FACEBOOK_APP_ID
        )

        context = super(SkigitBaseView, self).get_context_data(**kwargs)
        context['meta'] = meta
        context.update(mobile_api_request=kwargs.get('mobile_api_request', False))
        context.update(fee_business_skigit_logo=config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY,
                       fee_business_skigit_maintenance=config.FEE_BUSINESS_SKIGIT_MONTHLY_MAINTENANCE,
                       fee_skigit_view=config.FEE_SKIGIT_VIEW,
                       fee_skigit_plugin=config.FEE_SKIGIT_PLUGIN,
                       fee_social_network_post=config.FEE_SOCIAL_NETWORK_POST,
                       fee_skigit_share=config.FEE_SKIGIT_SHARE,
                       fee_logo_click=config.FEE_LOGO_CLICK,
                       fee_learn_more=config.FEE_LEARN_MORE,
                       fee_website_links_click=config.FEE_WEBSITE_LINKS_CLICK,
                       fee_skigit_embed_my_site=config.FEE_SKIGIT_EMBED_MY_SITE,
                       fee_skigit_embed_profile_page=config.FEE_SKIGIT_INTERNEL_EMBED)
        return context


def check_required_profile_fields(user,  user_profile):
    fields = [
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
    return fields


@method_decorator(ensure_csrf_cookie, name="dispatch")
class Home(SkigitBaseView):
    """ view for home
    """

    template_name = 'index.html'

    def get(self, request, extra_context=None, *args, **kwargs):
        id = request.GET.get('id', None)
        if id:
            kwargs.update(skigit_id=id)
        context = self.get_context_data(**kwargs)
        page_template = 'includes/entry_index_page.html'
        
        # get the most viewed video
        vid_most_viewed = VideoDetail.objects.filter(status=1, is_active=True)
        vid_most_viewed = cache.get_or_set('vid_most_viewed', vid_most_viewed.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)).order_by(
                '-view_count'))
        vid_most_viewed = vid_most_viewed[0] if vid_most_viewed.exists() else ''
         
        like_skigit = Like.objects.filter(user_id=request.user.id, status=True).values_list('skigit_id', flat=True)
        
        context.update({'page_template': page_template, 'vid_most_viewed':vid_most_viewed,})
                
        if request.is_ajax():
            videos_latest = VideoDetail.objects.filter(status=1, is_active=True)
            videos_latest = cache.get_or_set('video_latest', videos_latest.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        ).order_by(
            '-updated_date'))

            context.update({
                            'videos_latest': videos_latest,
                            'video_likes': like_skigit
                            })
        else:
            if request.user.is_authenticated:
                try:
                    user = User.objects.get(pk=request.user.id)
                    user_profile = Profile.objects.get(user=user)

                    if not user.groups.all():
                        # Remove this in FUTURE
                        # gen_obj = Group.objects.get_or_create(name="General User")
                        # user.groups.add(gen_obj[0])
                        return HttpResponseRedirect(reverse('manage-register-type'))

                    if user.is_staff and user.groups.all()[0].name == settings.SKIGIT_ADMIN:
                        return HttpResponseRedirect("admin_tools/dashboard/skigit_admin")
                    
                    if user.groups.all()[0].name == settings.BUSINESS_USER:
                        fields = check_required_profile_fields(user, user_profile)
                        if not all(fields):
                            messages.error(request,
                                           'You have not completed all fields or may have entered incorrect information. Please review your entries and error messages for correction. Click SAVE when done.')
                            raise ObjectDoesNotExist
                        elif not is_verified_business_user(user):
                            messages.error(request, 'You can only access your profile page until your account is verified. We will notify you when verified at which time, you will have full access to all Skigit features. Thank you for your patience.')
                            raise ObjectDoesNotExist
                        elif not user_profile.logo_img.filter(is_deleted=False).all():
                            messages.error(request, 'You must display at least one logo at all times. Please upload while this popup is displaying, then click OK.')
                            raise ObjectDoesNotExist
                        elif not Invoice.objects.filter(user=request.user, type='CreditCard',
                                                        is_deleted=False).exists() and not \
                                Invoice.objects.filter(user=request.user, type='PayPalAccount', is_deleted=False).exists():
                            messages.error(request, 'Payment information is not verified. Please verify payment method by '
                                                    'filling PayPal or Credit/Debit card details.')
                            raise ObjectDoesNotExist
                        elif request.user.profile.payment_method == '1' \
                                and not Invoice.objects.filter(user=request.user, type='CreditCard',
                                                               is_deleted=False).exists():
                            messages.error(request, 'Payment information is not verified. Please verify payment method by '
                                                    'filling PayPal or Credit/Debit card details.')
                            raise ObjectDoesNotExist
                        elif request.user.profile.payment_method == '0' \
                                and not Invoice.objects.filter(user=request.user, type='PayPalAccount',
                                                               is_deleted=False).exists():
                            messages.error(request, 'Payment information is not verified. Please verify payment method by '
                                                    'filling PayPal or Credit/Debit card details.')
                            raise ObjectDoesNotExist

                    elif user.is_superuser or (user.is_staff and is_user_general(user)) or is_user_general(user):
                        fields = check_required_profile_fields(user,  user_profile)
                        if not all(fields):
                            messages.error(request,
                                           'You have not completed all fields or may have entered incorrect information. Please review your entries and error messages for correction. Click SAVE when done.')
                            raise ObjectDoesNotExist
                    
                    else:
                        logout(request)
                        return HttpResponseRedirect('/')

                except ObjectDoesNotExist:
                    return HttpResponseRedirect('/profile')

                user_profile = Profile.objects.get(user=user)
                context.update({'user': user, 'user_profile': user_profile})

        if extra_context is not None:
            context.update(extra_context)
        if request.is_ajax():
            videos_template_name = 'includes/videos_list.html'
            videos_content = render_to_string(videos_template_name, context, request)
            context.update(home_videos=videos_content)
            self.template_name = page_template
        return render(request, self.template_name, context)


@csrf_exempt
@login_required(login_url='/login')
def skigit_friend_invite(request):
    videoId = request.POST.get('video_id', None)
    video = VideoDetail.objects.get(id=videoId, is_active=True)
    user = request.user
    context = {
        "friend_list": get_friends_list(user),
        'users': get_all_logged_in_users(),
        'skigit_list': get_share_list(user, video),
        "vid": video
    }
    return render(request, "includes/friends_share.html", context)

@ensure_csrf_cookie
@page_template('includes/entry_index_page.html')
def index(request, template='index.html', extra_context=None):

    # request.META['CSRF_COOKIE_USED'] = True
    id = request.GET.get('id', None)
    context = {}
    like_dict = []
    share_dict = []
    plug_dict = []
    vid_all = None
    vid_random = None
    # random video
    max_id = VideoDetail.objects.filter(status=1, is_active=True).order_by('-id')[0].id
    vid = True
    while vid is True:
        random_id = random.randint(1, max_id + 1)
        vid_random = VideoDetail.objects.filter(id__gte=random_id, status=1, is_active=True)

        if vid_random:
            vid_random = vid_random[0]
            vid = False
    # vid_latest_uploaded = VideoDetail.objects.select_related('skigit_id')
    if id:
        if VideoDetail.objects.filter(id=int(id), status=1, is_active=True).exists():
            vid_latest_uploaded1 = VideoDetail.objects.filter(id=int(id), status=1, is_active=True).order_by(
                '-updated_date')
            vid_latest_uploaded = VideoDetail.objects.exclude(id=int(id)).filter(status=1, is_active=True).order_by(
                '-updated_date')
            vid_latest_uploaded = list(chain(vid_latest_uploaded1, vid_latest_uploaded))
        else:
            vid_latest_uploaded = vid_random
    else:
        vid_latest_uploaded = vid_random

    videos_latest = VideoDetail.objects.select_related('skigit_id').filter(
            Q(receive_donate_sperk__in=[1, 2]) | Q(skigit_id__user__is_active=True)
        )
    if id:
        if videos_latest.filter(id=int(id), status=1, is_active=True).exists():
            videos_latest1 = videos_latest.filter(id=int(id), status=1, is_active=True).order_by('-updated_date')
            videos_latest = videos_latest.exclude(id=int(id)).filter(status=1, is_active=True).order_by('-updated_date')
            videos_latest = list(chain(videos_latest1, videos_latest))

        else:
            videos_latest = videos_latest.filter(status=1, is_active=True).order_by('-updated_date')
    else:
        videos_latest = videos_latest.filter(status=1, is_active=True).order_by('-updated_date')

    profile_dic = []
    for vid_profile in videos_latest:

        video_count = Like.objects.filter(skigit=vid_profile.skigit_id, status=True).count()
        like_dict.append({'id': vid_profile.id, 'count': video_count})
        video_share = Share.objects.filter(skigit_id=vid_profile, is_active=True).count()
        share_dict.append({'id': vid_profile.id, 'count': video_share})
        video_plug = VideoDetail.objects.filter(plugged_skigit=vid_profile.skigit_id, is_plugged=True, status=1).count()
        plug_dict.append({'id': vid_profile.id, 'count': video_plug})
        if vid_profile.made_by:
            us_profile = Profile.objects.get(user=vid_profile.made_by)
            if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                us_profile.made_by = vid_profile.made_by.id
                us_profile.business_logo = us_profile.logo_img.filter(is_deleted=False).all()[0]
                profile_dic.append(us_profile)
    profile_dic = list(set(profile_dic))
    ski_share_list = []
    for vid_data in videos_latest:
        sharObj = Share.objects.filter(skigit_id=vid_data, is_active=True, user=request.user.id).order_by('to_user', '-pk').distinct('to_user')
        for sh in sharObj:
            ski_share_list.append({'share_date': sh.created_date, 'username': sh.to_user.username, 'vid': sh.skigit_id_id})
    video_likes = Like.objects.filter(user_id=request.user.id, status=1)
    like_skigit = []
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
                #l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
            else:
                l_img = "{0}{1}".format(settings.STATIC_URL,'images/noimage_user.jpg')
            friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                'name': friends.user.get_full_name(), 'image': l_img})
    context.update({
        'video_likes': like_skigit,
        'like_count': like_dict,
        'video_share': share_dict,
        'video_plug': plug_dict,
        'vid_latest_uploaded': vid_latest_uploaded,
        'videos_latest': videos_latest,
        'default_logo': profile_dic,
        'friend_list': friend_list,
        'skigit_list': ski_share_list,
        'users': get_all_logged_in_users()
    })

    if request.user.is_authenticated:
        try:
            user = User.objects.get(pk=request.user.id)
            user_profile = Profile.objects.get(user=user)

            if not user.groups.all():
                # Remove this in FUTURE
                # gen_obj = Group.objects.get_or_create(name="General User")
                # user.groups.add(gen_obj[0])
                return HttpResponseRedirect(reverse('manage-register-type'))

            if user.is_staff and user.groups.all()[0].name == settings.SKIGIT_ADMIN:
                return HttpResponseRedirect("admin_tools/dashboard/skigit_admin")

            if user.is_superuser or (user.is_staff and is_user_general(user)) or is_user_general(user):
                fields = [
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
                    messages.error(request,
                                   'You have not completed all fields or may have entered incorrect information. Please review your entries and error messages for correction. Click SAVE when done.')
                    raise ObjectDoesNotExist
            elif user.groups.all()[0].name == settings.BUSINESS_USER:
                fields = [
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
                    messages.error(request,
                                   'You have not completed all fields or may have entered incorrect information. Please review your entries and error messages for correction. Click SAVE when done.')
                    raise ObjectDoesNotExist
                elif not is_verified_business_user(user):
                    messages.error(request, 'You can only access your profile page until your account is verified. We will notify you when verified at which time, you will have full access to all Skigit features. Thank you for your patience.')
                    raise ObjectDoesNotExist
                elif not user_profile.logo_img.filter(is_deleted=False).all():
                    messages.error(request, 'You must display at least one logo at all times. Please upload while this popup is displaying, then click OK.')
                    raise ObjectDoesNotExist
                elif not Invoice.objects.filter(user=request.user, type='CreditCard', is_deleted=False).exists() and not \
                        Invoice.objects.filter(user=request.user, type='PayPalAccount', is_deleted=False).exists():
                    messages.error(request, 'Payment information is not verified. Please verify payment method by '
                                            'filling PayPal or Credit/Debit card details.')
                    raise ObjectDoesNotExist
                elif request.user.profile.payment_method == '1' \
                        and not Invoice.objects.filter(user=request.user, type='CreditCard', is_deleted=False).exists():
                    messages.error(request, 'Payment information is not verified. Please verify payment method by '
                                            'filling PayPal or Credit/Debit card details.')
                    raise ObjectDoesNotExist
                elif request.user.profile.payment_method == '0' \
                        and not Invoice.objects.filter(user=request.user, type='PayPalAccount', is_deleted=False).exists():
                    messages.error(request, 'Payment information is not verified. Please verify payment method by '
                                            'filling PayPal or Credit/Debit card details.')
                    raise ObjectDoesNotExist
            else:
                logout(request)
                return HttpResponseRedirect('/')

        except ObjectDoesNotExist:
            return HttpResponseRedirect('/profile')

        user_profile = Profile.objects.get(user=user)
        context.update({'user': user, 'user_profile': user_profile})

        if extra_context is not None:
            context.update(extra_context)
        return render(request, template, context)

    elif request.method == 'POST' and 'login_submit' in request.POST:
        username = request.POST.get('log', None)
        password = request.POST.get('pwd', None)
        user = authenticate(username=username, password=password)
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                # An inactive account was used - no logging in!
                context = RequestContext(request)
                context.update(csrf(request))
                context.update({'vid_latest_uploaded': vid_latest_uploaded,
                                'vid_all': vid_all,
                                'videos_latest': videos_latest,
                                'video_likes': like_skigit,
                                'like_count': like_dict,
                                'video_share': share_dict,
                                'video_plug': plug_dict,
                                'default_logo': profile_dic})
                context.update({
                    'login_error': 'Your Skigit account is disabled.'
                })

                if extra_context is not None:
                    context.update(extra_context)
                return render(template, context)

        else:
            # Bad login details were provided. So we can't log the user in.
            context.update(csrf(request))
            msg = "Invalid login details: {0}, {1}".format(username, password)
            context.update({'login_error': msg})
            context.update({'vid_latest_uploaded': vid_latest_uploaded,
                            'videos_latest': videos_latest,
                            'video_likes': like_skigit,
                            'like_count': like_dict,
                            'video_share': share_dict,
                            'video_plug': plug_dict,
                            'default_logo': profile_dic
                            })
            if extra_context is not None:
                context.update(extra_context)
            return render(request, template, context)

    else:

        if extra_context is not None:
            context.update(extra_context)
        return render(request, template, context)

class CategoryAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def list(self, request):
        result = {'status': '',
                  'message': ''}

        try:
            category = Category.objects.all()
            serializer = self.get_serializer(category, many=True)
            result.update(status='success',
                          message='',
                          data=serializer.data)
        except Exception as exc:
            result.update(status='error',
                          message='Category list not found!')
        return Response(result)

class SubjectCategoryAPIView(generics.ListAPIView):
    serializer_class = SubjectCategorySerializer

    def list(self, request):
        result = {'status': '',
                  'message': ''}

        try:
            category = SubjectCategory.objects.all()
            serializer = self.get_serializer(category, many=True)
            result.update(status='success',
                          message='',
                          data=serializer.data)
        except Exception as exc:
            result.update(status='error',
                          message='Subject Category list not found!')
        return Response(result)

class ShareManageDeeplinkView(RedirectView):
    permanent = True

    def get_redirect_url(self, *ar, **kwargs):
        query_params = self.request.GET
        #category = query_params.get('category', '')
        video_id = query_params.get('contentid', '')
        url_name = reverse('index')

        #if category == 'SKIGIT':
        if video_id:
            url_name = reverse('skigit_data', kwargs={'pk': video_id})
        return url_name


class UrlExistView(View):
    '''
        Return the url exist or not!
    '''

    def get(self, request):
        '''
            Return "true" if exist or throws error message
        '''

        error_message = "I Bought My Awesome URL is invalid. Please enter a valid URL."
        url = self.request.GET.get('bought_at', '').lower().strip()
        url_valid = check_valid_url(url)
        message = "true" if url_valid else error_message
        return JsonResponse(message, safe=False)


class UrlListAPIView(generics.ListAPIView):
    """
    Get all urls for the bug report management API.
    """
    serializer_class = UrlSerializer

    def list(self, request):
        result = {'status': '',
                  'message': ''}
        data = []
        try:
            """urls = get_resolver().reverse_dict.items()
            url_list = [{'name': name,
                         'url': '{}/{}'.format(settings.HOST, url_pattern[1])}
                        for name, url_pattern in urls if isinstance(name, str)]
            serializer = self.get_serializer(url_list, many=True)"""
            general_site_data = GeneralSiteData.objects.all().order_by('-id')
            if general_site_data.exists():
                general_site_data = general_site_data[0]
                data = json.loads(general_site_data.bug_category_url)
            result.update(status='success',
                          message='',
                          data=data)
        except Exception as exc:
            logger.error("UrlListAPIView: URL list throws error %s", exc)
            result.update(status='error',
                          message='URL list throws error!')
        return Response(result)


class AdminDataMigrateAPIView(generics.ListAPIView):
    """
    Get all urls for the bug report management API.
    """
    #permission_classes = (CustomIsAuthenticated,)

    def list(self, request):
        result = {'status': '',
                  'message': ''}
        constance_values = {}
        data = {}
        try:
            email_template_data = EmailTemplate.objects.all().values('template_name', 'subject',
                                                                     'html_template', 'description',
                                                                     'template_key')
            constance_name = constance_settings.CONFIG.keys()
            for key in constance_name:
                constance_values[key] = getattr(config, key)
            data.update(email_template_data=email_template_data,
                        constance_data=constance_values)
            result.update(data=data)
        except Exception as exc:
            logger.error("Admin Source data migration ListAPIView: list throws error %s", exc)
            result.update(status='error',
                          message='List throws error!')
        return Response(result)

class AdminDataMigrateUpdateAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        """
        :param request: Now the mailpost and constance values are mograted from Dev!
        :return:
        """

        result = {'status': '', 'message': ''}
        dev_site_host = '{}'.format(settings.DEV_HOST)
        source_data = requests.get('{}/api/v1/migrate/admin/'.format(dev_site_host)).json()
        data = source_data['data']
        for source in data['email_template_data']:
            EmailTemplate.objects.filter(template_key=source['template_key']).update(template_name=source['template_name'].replace('dev.skigit.com', 'skigit.com'),
                                                                                     subject=source['subject'].replace('dev.skigit.com', 'skigit.com'),
                                                                                     html_template=source['html_template'].replace('dev.skigit.com', 'skigit.com'),
                                                                                     description=source['description'].replace('dev.skigit.com', 'skigit.com'))
        for name, value in data['constance_data'].items():
            setattr(config, name, value)
        result.update(status='success',
                      message='All admin data are migrated from Dev to Prod successfully!')
        return Response(result)

class sendOtpAPIView(views.APIView):

    def post(self, request):
        """
        Sent an OTP to user
        """
        
        result = {'status': '', 'message': '', 'secret': "000000000"}
        phone_number = request.data.get('phone_number')

        otp_obj = generateOTP()

        sendTwilioSMS(phone_number,otp_obj) ## send sms to user

        result.update(status='success',
                        secret=str(otp_obj.get("secret")),
                        message='OTP sent successfully!')
        return Response(result)

class verifyOtpAPIView(views.APIView):

    def post(self, request):
        """
        Verify an OTP. Is it true or false
        """

        result = {'status': '','verify': None}
        
        otp = request.data.get('otp')

        secret = request.data.get('secret')
          
        isValid = verifyOTP(secret,otp)

        result.update(status='success',
                        verify=isValid)
        return Response(result)

class isPhoneValidAPIView(views.APIView):

    def post(self, request):
        """
        Validate Phone Number
        """
        
        result = {'status': '', 'isValid': False}
        phone_number = request.data.get('phone_number')
        country_code = request.data.get('country_code')
        isValid = checkPhoneValidity(phone_number,country_code)

        result.update(status='success',
                        isValid=isValid)
        return Response(result)     


def redirect_page_not_found(request, exception=None):
    template_name = 'errors/404.html'
    return render(request, template_name)

def redirect_server_error(request, exception=None):
    template_name = 'errors/500.html'
    return render(request, template_name)
