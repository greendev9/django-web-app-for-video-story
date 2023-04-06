import json
import logging
import datetime
import ast

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import (PasswordResetView, PasswordResetConfirmView,
                                       PasswordChangeView)
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.generic.edit import DeleteView
from django.views import View
from heapq import merge

from urllib3 import HTTPResponse
from sorl.thumbnail import get_thumbnail
from django.template.context_processors import csrf
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import striptags

from django_countries import countries

from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework import (status, views, generics, mixins,
                            permissions, viewsets)
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_auth.views import PasswordResetConfirmView as PWResetAPIConfirmView
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter, TwitterAPI
from instagram.views import InstagramOAuth2Adapter
from allauth.socialaccount.providers.linkedin_oauth2.views import LinkedInOAuth2Adapter
from rest_auth.social_serializers import TwitterLoginSerializer
from user.SocialLoginView import SocialLoginView

from core.utils import (is_user_general, is_user_business,
                        client_paypal_token, client_token,
                        get_object_or_None, register_type_required,
                        payment_required, require_filled_profile, get_all_logged_in_users,
                        CustomIsAuthenticated, notify_password_change, register_confirm, generateTokenFromCode,
                        delete_user_account, user_invoices_cleared, alpha_numeric_str, states_list_By_country, require_admin, 
                        is_verified_business_user,sendTwilioSMS,phoneToIntFormat)
from friends.models import Friend, Embed, FriendInvitation
from invoices.models import Invoice, BusinessLogoInvoice
from skigit.models import Video, VideoDetail, Like
from skigit.serializers import VideoDetailSerializer
from social.models import Share
from user.models import Profile, ProfileUrl
from user.forms import (RegistrationForm, UserForm, ProfileForm, BusinessUserProfileForm, UserApiForm,
                        BusinessUserProfileApiForm, ProfileApiForm, CustomPasswordResetForm, TwoFactorAuthForm)
from user.serializers import (UserSerializer, RegisterSerializer, ProfileSerializer,
                              ProfileBusinessSerializer, ProfileNotificationSerializer,
                              LoginSerializer, PasswordResetEmailSerializer, UserAccountDeleteSerializer,
                              BusinessProfileDetailSerializer, ProfileUrlSerializer, BusinessLogoSerializer, ExtraProfileImageSerializer,
                              SperkListSerializer, ProfileFriendSerializer, api_request_images, CustomTokenObtainPairSerializer,
                              LoginResponseSerializer, TwoFaSerializer, BaseAPISerialier, EmailSerializer)
from mailpost.models import EmailTemplate
from skigit.views import (check_email_exists, get_user_statistics, manage_sperk, get_business_logos,
                          get_profile_extra_images, upload_profile_image, upload_coupon_image, upload_business_logo,
                          get_sperk_profile_detail, get_company_urls, get_user_plugged_videos, get_followers, upload_extra_profile_image)
from invoices.serializers import PaymentMethodCardSerializer, PaymentMethodPaypalSerializer
from invoices.views import update_donate_unpaid_invoices
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification
from django.utils import timezone

logger = logging.getLogger('User')

### Generic functions ###


def check_profile_urls(url1, url2, url3, url4, url5):
    """
    :param url1:
    :param url2:
    :param url3:
    :param url4:
    :param url5:
    :return: Check any one url is filled and it is valid one!
    """
    result = {}
    status = ''
    message = ''
    if not any([url1, url2, url3, url4, url5]):
        status = 'error'
        message = 'Profile url - Please enter any one profile url and url description'
    else:
        for i in [url1, url2, url3, url4, url5]:
            if i and (not i.startswith('http://') and not i.startswith('https://')):
                status = 'error'
                message = 'Profile url - Please enter valid profile url'
    result.update(status=status,
                  message=message)
    return result


def add_user_group(user, register_type):
    '''

    :param user: Cur user
    :param register_type: general/business
    :return: True if group is added!
    '''

    group_name = ''
    if register_type == 'general':
        group_name = settings.GENERAL_USER
    elif register_type == 'business':
        group_name = settings.BUSINESS_USER
    group = get_object_or_None(Group, name=group_name)
    if group:
        user.groups.clear()
        user.groups.add(group)
        logger.error(user.groups.all())
        return True
    return False


def remove_business_logo(user_id, logo_id):
    context = {}
    try:
        user = get_object_or_None(User, id=user_id)
        logos = user.profile.logo_img.filter(id=logo_id)
        if logos.exists():
            # on delete logo image, set new logo for all linked skigits
            next_logo = user.profile.logo_img.exclude(id=logo_id)
            if next_logo.exists():
                next_logo = next_logo.order_by('id').first()
                VideoDetail.objects.filter(business_logo=logos.first()).update(
                    business_logo=next_logo)
                BusinessLogoInvoice.objects.filter(
                    business_logo=logos.first()).update(business_logo=next_logo)
                logos.delete()
                context.update(
                    {'is_success': True, 'message': "Logo was deleted successfully"})
            else:
                context.update({'is_success': False, 'message': 'You cannot delete your master logo. If you delete this logo, all Skigits using it will not be able to display it for your business. You will still be charged applicable fees during this time.'})
        else:
            context.update(
                {'is_success': False, 'message': "Logo was not deleted!"})
    except Exception as exc:
        logger.error("Logo delete throws error: ", exc)
        context.update(
            {'is_success': False, 'message': "The logo was not deleted!"})
    return context


def remove_profile_image(user_id, image_type, image_id):
    context = {}

    try:
        user = get_object_or_None(User, id=user_id)
        if image_id:
            user.profile.extra_profile_img.filter(id=image_id).delete()
        elif image_type == 'profile':
            profile = user.profile
            profile.profile_img = None
            profile.save()
            user.profile.profile_img.delete()
        elif image_type == 'coupon':
            profile = user.profile
            profile.coupan_image = None
            profile.save()
            user.profile.coupan_image.delete()
        else:
            context.update(
                {'is_success': False, 'message': "The image is not there!"})
            return context
        context.update(
            {'is_success': True, 'message': "The image was deleted successfully!"})
    except Exception as exc:
        logger.error("The image delete throws error: ", exc)
        context.update(
            {'is_success': False, 'message': "The image was not deleted!"})
    return context


@method_decorator(login_required(login_url='/login'), name='dispatch')
@method_decorator(payment_required, name='dispatch')
@method_decorator(require_filled_profile, name='dispatch')
class UserProfileDisplay(TemplateView):
    def get(self, request, username):
        context = {}
        try:
            request_user = User.objects.get(username=username, is_active=True)
        except ObjectDoesNotExist:
            messages.error(
                request, "We're Sorry. This account is no longer active on Skigit.")
            return HttpResponseRedirect('/')  # HttpResponseRedirect
        if not request_user.profile.is_completed['status']:
            messages.error(
                request, "We're Sorry. This account is no longer active on Skigit.")
            return HttpResponseRedirect('/')
        busniess_logo = []
        like_dict = []
        friend_list = []
        ski_share_list = []
        company_url = None
        if Profile.objects.filter(user=request_user).exists():
            request_user_profile = Profile.objects.get(user=request_user)
            extra_profile_img = request_user_profile.extra_profile_img.all()
            extra_profile_img_url = [get_thumbnail(profile_img.profile_img, '200x200', crop='center', quality=100, format='PNG').url
                                     for profile_img in extra_profile_img]

        if request_user.is_superuser or (
                request_user.is_staff and is_user_general(request_user)) or is_user_general(request_user):
            user_template = 'profile/general_user_profile.html'
        elif request_user.groups.all()[0].name == settings.BUSINESS_USER:
            # user_template = 'profile/general_user_profile.html' if self.request.GET.get('view-general', 'no') == 'yes' else \
            #                'profile/business_user_profile.html'
            user_template = 'profile/general_user_profile.html'
        else:
            messages.error(request,
                           'Sorry, Your Request User Account Group Type was not found.')
            return HttpResponseRedirect('/')

        if request.user.is_authenticated:
            user = request.user
            if is_user_business(request_user):
                for bb_logo in request_user_profile.logo_img.filter(is_deleted=False).all():
                    bb_logo.img_id = bb_logo.id
                    bb_logo.l_img = get_thumbnail(
                        bb_logo.logo, '200x200', crop='center', quality=100, format='PNG').url
                    busniess_logo.append(bb_logo)
                    company_url = ProfileUrl.objects.filter(
                        user=request_user_profile.user)
                context.update({'company_url': company_url})

            user_profile = Profile.objects.get(user=request_user)

            if Embed.objects.filter(to_user=request_user_profile.user,
                                    is_embed=True).exists():
                embed_skigit_list = Embed.objects.filter(
                    to_user=request_user_profile.user,
                    is_embed=True).values_list('skigit_id', flat=True)

                if request.user.is_authenticated:
                    if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id),
                                             status=1).exists():
                        f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id),
                                                       status=1)
                        from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user',
                                                                                               flat=True).distinct()
                        to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user',
                                                                                           flat=True).distinct()
                        fr_list = list(merge(from_user_list, to_user_list))
                        friends_detail = Profile.objects.filter(
                            user__id__in=fr_list).order_by('user__username')
                        for friends in friends_detail:
                            if friends.profile_img:
                                l_img = get_thumbnail(
                                    friends.profile_img, '200x200', crop='center', quality=99, format='PNG').url
                            else:
                                l_img = "{0}{1}".format(
                                    settings.STATIC_URL, 'skigit/detube/images/noimage_user.jpg')
                            friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                                'name': friends.user.get_full_name(), 'image': l_img})
                    video_likes = Like.objects.filter(
                        user_id=request.user.id, status=True)
                    for likes in video_likes:
                        like_dict.append(likes.skigit_id)
                vid = VideoDetail.objects.select_related('skigit_id').filter(skigit_id__id__in=embed_skigit_list,
                                                                             status=1)
                serializer = VideoDetailSerializer(vid, many=True)
                for vid_data in vid:
                    sharObj = Share.objects.filter(skigit_id=vid_data,
                                                   is_active=True,
                                                   user=request_user_profile.user).order_by(
                        'to_user', '-pk').distinct('to_user')
                    for sh in sharObj:
                        ski_share_list.append(
                            {'share_date': sh.created_date, 'username': sh.to_user.username,
                             'vid': sh.skigit_id_id})
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


class LoginViewAPI(views.APIView):
    def post(self, request, format=None):
        data = json.loads(request.body.decode())

        email = data.get('email', None)
        password = data.get('password', None)

        account = authenticate(email=email, password=password)

        if account is not None:
            if account.is_active:
                login(request, account)

                serialized = UserSerializer(account)

                return Response(serialized.data)
            else:
                return Response({
                    'status': 'Unauthorized',
                    'message': 'This account has been disabled.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'status': 'Unauthorized',
                'message': 'Username/password combination invalid.'
            }, status=status.HTTP_401_UNAUTHORIZED)


def sendTwoFaNotification(user, retry=1):
    code = alpha_numeric_str()
    profile = user.profile
    profile.two_fa_code = code
    profile.two_fa_retry = retry
    profile.two_fa_code_expire_at = datetime.datetime.now() + \
        datetime.timedelta(minutes=10)
    profile.save()
    if is_user_business(user):
      phone_number = phoneToIntFormat(profile.contact_phone,profile.country)
    else:
      phone_number = phoneToIntFormat(profile.phone_num,profile.country)

    sendTwilioSMS(phone_number,code) ## sending sms to user

    if user.profile.two_fa_by_email:
        try:
            EmailTemplate.send(
                template_key="user_two_fa_login",
                emails=user.email,
                context={"code": code, "host": ''.join(settings.HOST)}
            )
        except:
            pass

    if user.profile.two_fa_by_app:
        devices = FCMDevice.objects.filter(user=user)
        message = Message(
            notification=Notification(
                title="Your Skigit Login OTP is {}".format(code),
                body="Provide this code within the next 10 minutes to authenticate your activity",
            ),
        )
        devices.send_message(message)


class LoginView(TemplateView):

    def get(self, request):
        return render(request, 'user/login.html', {})

    def post(self, request, extra_context=None):
        data = request.POST
        username = data.get('email', None)
        password = data.get('password', None)
        user = get_user(username, password)

        if user is not None:
            if user.is_active:
                request.session['user_id'] = user.id
                profile = user.profile
                if profile.two_fa_by_email or profile.two_fa_by_app:
                    sendTwoFaNotification(user)

                    return JsonResponse({
                        'is_success': True,
                        'status': 'CodeSent',
                        'message': 'Enter code sent to you by email and/or mobile app notification'
                    })
                else:
                    login(request, user)

                    return JsonResponse({
                        'is_success': True,
                        'status': 'Authorized',
                        'message': 'Your login was successful!'
                    })
            else:
                return JsonResponse({
                    'is_success': False,
                    'status': 'Unauthorized',
                    'message': 'Your account has been deactivated. Email <a href="mailto:accounts@skigit.com">accounts@skigit.com</a> to reactivate.'
                })
        else:
            return JsonResponse({
                'is_success': False,
                'status': 'Unauthorized',
                'message': 'Your username and/or password are incorrect. Please try again.'
            })


@method_decorator(login_required(login_url='/login'), name="dispatch")
class ManageRegisterType(TemplateView):
    template_name = 'registration/registration_type.html'

    def get_context_data(self, *ar, **kwargs):
        context = super(ManageRegisterType,
                        self).get_context_data(*ar, **kwargs)
        Profile.objects.get_or_create(user=self.request.user)
        context.update(social_register=True)
        context.update(
            social_account=self.request.user.socialaccount_set.first())
        return context

    def post(self, request):
        status = add_user_group(user=self.request.user,
                                register_type=request.POST.get('acc_type', '').lower())
        if status:
            return HttpResponseRedirect(reverse('user_profile'))
        return HttpResponseRedirect('/')


class SocialRegisterDelete(View):

    def post(self, request, pk):
        User.objects.filter(id=pk).delete()
        request.session.flush()
        return JsonResponse({
            'is_success': True,
            'message': 'The user is deleted!'
        })


class RegisterType(TemplateView):
    def get(self, request):
        context = {}
        if request.user.is_authenticated:
            return HttpResponseRedirect('/')
        else:
            context.update(csrf(request))
            return render(request, 'registration/registration_type.html', context)

    def post(self, request):
        context = {}
        data = request.POST
        register_type_error_template = None

        if 'register_type' in data:
            acc_type = data.get('acc_type', None)

            if acc_type and acc_type in ['general', 'business']:
                acct_values = {'general': {'acc_type': 'general', 'template_name': 'registration/register_as_general_user.html'},
                               'business': {'acc_type': 'business', 'template_name': 'registration/register_as_business_user.html'}}
                form = RegistrationForm()
                context.update(form=form, acc_type=acct_values[acc_type]['acc_type'])
                return render(request,
                              acct_values[acc_type]['template_name'],
                              context)
            else:
                context.update(csrf(request))
                return render(request,
                              'registration/registration_type.html', context)
        elif 'register_as_general_user' in data:
            acc_type = 'general'
            register_type_error_template = 'registration/register_as_general_user.html'
        elif 'register_as_business_user' in data:
            acc_type = 'business'
            register_type_error_template = 'registration/register_as_business_user.html'
        else:
            context.update(csrf(request))
            return render(request,
                          'registration/registration_type.html',
                          context)

        form = RegistrationForm(data)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            cleaned_data.update(accType=acc_type)
            serializer = RegisterSerializer(data=cleaned_data)
            if serializer.is_valid():
                user = serializer.save(request=request)
                context.update({'user': user})

            return render(request,
                          'registration/register_success.html',
                          context)
        else:
            context.update({'form': form})
            return render(request,
                          register_type_error_template,
                          context)


class RegisterConfirm(TemplateView):

    def get(self, request, activation_key=None):
        result = register_confirm(activation_key)
        status = result['status']
        if status == 'success':
            messages.success(request, result['message'])
        elif status == 'error':
            messages.error(request, result['message'])
        else:
            messages.error(request, 'Invalid activation link.')
        redirect_to = result['redirect_to'] if 'redirect_to' in result else ''
        return HttpResponseRedirect(redirect_to)


class Reset(PasswordResetView):
    html_email_template_name = 'registration/password_reset_email.html',
    subject_template_name = 'registration/recovery_email_subject.txt',
    success_url = reverse_lazy('reset_success')
    form_class = CustomPasswordResetForm


class ResetConfirm(PasswordResetConfirmView):
    success_url = reverse_lazy('reset_done')


class CustomPasswordResetConfirmAPIView(PWResetAPIConfirmView):

    def post(self, request, *args, **kwargs):
        result = {'status': '', 'message': ''}
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            result.update(status='success', message=_(
                "Password has been reset with the new password."))
        else:
            errors = serializer.errors
            for k, v in errors.items():
                if k == 'token':
                    result.update(status='error',
                                  message="{0} - {1}".format(k, v[0]))
                else:
                    result.update(status='error',
                                  message='Password is invalid. Password length should be minimum 8 characters.'
                                  'Password should have atleast one number and one symbol. '
                                  'Password should not have the username value.')
                break
        return Response(result)


@method_decorator(login_required(login_url='/login'), name="dispatch")
@method_decorator(register_type_required, name="dispatch")
class UserProfile(TemplateView):
    """
            User Profile View
    """

    def get(self, request):
        payment_environment = 'production' if settings.PROD else 'sandbox'
        context = {'payment_environment': payment_environment}
        user = request.user

        try:
            is_business = is_user_business(user)
        except:
            is_business = False
        context['is_business'] = is_business
        try:
            is_general = is_user_general(user)
        except:
            is_general = False
        context['is_general'] = is_general

        context['backend_name'] = cache.get('backend')
        profile, created = Profile.objects.get_or_create(user=user)

        if is_business:
            payment_data = self.get_payment_detail(request)
            context.update(payment_data)
            profile_completed = profile.is_completed
            if not profile_completed['status']:
                messages.error(request, profile_completed['message'])

            form1 = UserForm(instance=user)
            form2 = BusinessUserProfileForm(instance=user.profile)

            profile_url = ProfileUrl.objects.get_or_create(user=user)
            profile_url = profile_url[0]

            disc1 = profile_url.disc1
            url1 = profile_url.url1
            disc2 = profile_url.disc2
            url2 = profile_url.url2
            disc3 = profile_url.disc3
            url3 = profile_url.url3
            disc4 = profile_url.disc4
            url4 = profile_url.url4
            disc5 = profile_url.disc5
            url5 = profile_url.url5
        elif user.is_superuser or (user.is_staff and is_general) or is_general:
            form1 = UserForm(instance=user)
            form2 = ProfileForm(instance=profile)
        else:
            logout(request)
            return HttpResponseRedirect('/')

        context['backend_name'] = cache.get('backend')

        context.update(csrf(request))
        context['form1'] = form1
        context['form'] = form2
        context['user'] = user
        context['state_list'] = states_list_By_country(profile.country)
        context['user_profile'] = profile
        context['is_business'] = is_business
        context['verified_business'] = is_verified_business_user(user)
        if profile.profile_img:
            profile_url = request.build_absolute_uri(
                profile.profile_img.url)
            context['profile_image'] = profile_url

        if is_business:
            context['disc1'] = disc1
            context['url1'] = url1
            context['disc2'] = disc2
            context['url2'] = url2
            context['disc3'] = disc3
            context['url3'] = url3
            context['disc4'] = disc4
            context['url4'] = url4
            context['disc5'] = disc5
            context['url5'] = url5

        return render(request, 'profile/basic_profile.html', context)

    def post(self, request):
        context = {}
        user = request.user
        user_profile = user.profile

        try:
            is_business = is_user_business(user)
        except:
            is_business = False
        context['is_business'] = is_business
        try:
            is_general = is_user_general(user)
        except:
            is_general = False
        context['is_general'] = is_general
        context['backend_name'] = cache.get('backend')
        form1 = UserForm(request.POST, instance=user)
        incentive_amount = user_profile.incetive_val
        post_data = request.POST
        if is_business:
            form2 = BusinessUserProfileForm(
                request.POST, request.FILES, instance=user_profile)
            payment_data = self.get_payment_detail(request)
            context.update(payment_data)
            disc1 = post_data.get('disc1', None)
            url1 = post_data.get('url1', None)
            disc2 = post_data.get('disc2', None)
            url2 = post_data.get('url2', None)
            disc3 = post_data.get('disc3', None)
            url3 = post_data.get('url3', None)
            disc4 = post_data.get('disc4', None)
            url4 = post_data.get('url4', None)
            disc5 = post_data.get('disc5', None)
            url5 = post_data.get('url5', None)
            # set custom busines type to null if other option is not selected
            if post_data.get('business_type') != 'OS':
                request.POST._mutable = True
                request.POST.update({'custom_business_type': None})

        elif user.is_superuser or (user.is_staff and is_general) or is_general:
            form2 = ProfileForm(post_data, request.FILES,
                                instance=user_profile)
        else:
            logout(request)
            return HttpResponseRedirect('/')

        if form1.is_valid() and form2.is_valid():

            form1.save()
            form2.save()
            if is_business:
                profile_url = ProfileUrl.objects.get_or_create(user=user)
                profile_url = profile_url[0]
                profile_url.disc1 = disc1
                profile_url.url1 = url1
                profile_url.disc2 = disc2
                profile_url.url2 = url2
                profile_url.disc3 = disc3
                profile_url.url3 = url3
                profile_url.disc4 = disc4
                profile_url.url4 = url4
                profile_url.disc5 = disc5
                profile_url.url5 = url5
                profile_url.save()
                if form2.cleaned_data['incetive_val'] != incentive_amount:
                    update_donate_unpaid_invoices(user)

            logo_images = user_profile.logo_img.filter(is_deleted=False).count()
            extra_profile_images = user_profile.extra_profile_img.all().count()
            if (not logo_images) and is_business:
                messages.error(
                    request, 'You must display at least one logo at all times. Please upload while this popup is displaying, then click OK.')
            elif logo_images > 5:
                messages.error(request, 'Max 5 Business Logo allowed.')
                for i in range(5, logo_images):
                    user_profile.logo_img.filter(
                        is_deleted=False).last().delete()
            elif extra_profile_images > 5:
                messages.error(request, 'Max 5 Profile Images allowed.')
                for i in range(5, extra_profile_images):
                    user_profile.extra_profile_img.last().delete()
            elif is_business and not Invoice.objects.filter(user=user, type='CreditCard',
                                                            is_deleted=False).exists() and not \
                    Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False).exists():
                messages.error(request, 'Payment information is not verified. Please verify payment method by '
                               'filling PayPal or Credit/Debit card details.')
            elif is_business and user_profile.payment_method == '1' \
                    and not Invoice.objects.filter(user=user, type='CreditCard', is_deleted=False).exists():
                messages.error(request, 'Payment information is not verified. Please verify payment method by '
                               'filling PayPal or Credit/Debit card details.')
            elif is_business and user_profile.payment_method == '0' \
                    and not Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False).exists():
                messages.error(request, 'Payment information is not verified. Please verify payment method by '
                               'filling PayPal or Credit/Debit card details.')
            else:
                messages.success(request, 'Profile was updated successfully!')

            if Profile.objects.filter(user=user, email_sent=False).exists():
                user_profile = user.profile

                Profile.objects.filter(
                    user=user).update(email_sent=True)
                confirm_path = '/admin/auth/user/%s/' % user.id

                confirm = request.build_absolute_uri(confirm_path)

                if is_business:

                    domain = request.build_absolute_uri()
                    x = domain.replace("profile/", "")

                    context_tmp = {}
                    context_tmp['user'] = user
                    docs_array = user_profile.business_doc.all()

                    business_doc = ''

                    for doc in docs_array:
                        business_doc += business_doc + x + doc.doc + "<br>"

                    context_tmp.update(businessUser=user_profile,
                                       business_doc=business_doc,
                                       host=''.join(settings.HOST))
                    EmailTemplate.send(
                        template_key="new_business_user_verification",
                        emails=settings.EMAIL_HOST_USER,
                        context=context_tmp
                    )
                else:
                    EmailTemplate.send(
                        template_key="account_verification_task_admin",
                        emails=settings.EMAIL_HOST_USER,
                        context={
                            "confirm_link": confirm,
                            "username": user.username
                        }
                    )

            return HttpResponseRedirect(reverse('user_profile'))

        else:
            # context['backend_name'] = cache.get('backend')
            #user_profile = user.profile

            # context.update(csrf(request))
            context['form1'] = form1
            context['form'] = form2
            context['user'] = user
            context['user_profile'] = user_profile
            context['is_business'] = is_business
            if user_profile.profile_img:
                profile_url = request.build_absolute_uri(
                    user_profile.profile_img.url)
                context['profile_image'] = profile_url

            if is_business:
                context['disc1'] = disc1
                context['url1'] = url1
                context['disc2'] = disc2
                context['url2'] = url2
                context['disc3'] = disc3
                context['url3'] = url3
                context['disc4'] = disc4
                context['url4'] = url4
                context['disc5'] = disc5
                context['url5'] = url5
            return render(request, 'profile/basic_profile.html', context)

    def get_payment_detail(self, request):
        """
        Get the payment data based on the user invoice. If not get the token from BT!
        :param request:
        :return: payment data with tokens!
        """
        payment_data = {}
        user = request.user

        if Invoice.objects.filter(user=user, type='CreditCard', is_deleted=False).exists():
            inv_obj = Invoice.objects.filter(
                user=user, type='CreditCard', is_deleted=False)
            payment_data['card_found'] = True
            payment_data['card'] = str(
                '%06d*****%04d') % (int(inv_obj[0].first_6), int(inv_obj[0].last_4))
            payment_data['invoice_data'] = inv_obj
        else:
            payment_data['card_found'] = False
        if Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False).exists():
            paypal_obj = Invoice.objects.filter(
                user=user, type='PayPalAccount', is_deleted=False)
            payment_data['pay_pal_account_found'] = True
            payment_data['paypal_invoice_data'] = paypal_obj
        else:
            payment_data['pay_pal_account_found'] = False

        try:
            cc_token = client_token(request)
            pay_pal_token = client_paypal_token(request)
            payment_data['client_token'] = cc_token
            payment_data['pay_pal_client_token'] = pay_pal_token
        except Exception as exc:
            logger.error("Braintree generate token error : ", exc)

        return payment_data


class LogoutUser(TemplateView):

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, 'You have successfully logged out')
        return render(request, 'user/logout.html', {'logout_message': 'You have successfully logged out'})


#### REST API Views ####

class CustomTokenObtainPairView(TokenViewBase):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        result = {'status': '',
                  'message': ''}

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            result.update(status='success',
                          data=data['data'])
        except TokenError as e:
            result.update(status='error',
                          message=InvalidToken(e.args[0]))
        if serializer.validated_data['status_code'] == 401:
            result.update(status='error',
                          message='The username or password is invalid!')
        return Response(result)


class RegisterViewSet(viewsets.ViewSet):
    """
    API endpoint that allows user to register.
    """

    serializer_class = RegisterSerializer

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save(request=request)
            result.update(status='success',
                          message='An account activation link was sent to the email address.'
                          'Please click the link and activate your account now!',
                          data={'user_id': user.id,
                                'user_name': user.username,
                                'email': user.email})
        else:
            errors = serializer.errors
            for k, v in errors.items():
                result.update(status='error',
                              message="{0} - {1}".format(k, v[0]))
                break
        return Response(result)


class AccountImageUploadAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        upload_type = data.get('type', '')
        user = get_object_or_None(User, id=user_id)
        file_field_name = 'file'

        try:
            if upload_type == 'profile_image':
                response_data = upload_profile_image(user, files=request.FILES,
                                                     file_field_name=file_field_name,
                                                     api_request=True)
            elif upload_type == 'coupon_image':
                response_data = upload_coupon_image(user, files=request.FILES,
                                                    file_field_name=file_field_name,
                                                    api_request=True)
            elif upload_type == 'business_logo':
                response_data = upload_business_logo(user, files=request.FILES,
                                                     file_field_name=file_field_name,
                                                     api_request=True)
            elif upload_type == 'extra_profile_image':
                response_data = upload_extra_profile_image(user, files=request.FILES,
                                                           file_field_name=file_field_name,
                                                           api_request=True)
        except Exception as exc:
            logger.error("Account Image is not uploaded: ", exc)
            response_data = {'is_success': False,
                             'message': 'Account image was not uploaded successfully. Please try again.'}
        status = 'success' if response_data['is_success'] else 'error'
        message = response_data['message'] if 'message' in response_data else ''
        data = response_data['data'] if 'data' in response_data else {}
        result.update(status=status,
                      message=message,
                      data=data)
        return Response(result)


class AddUserAccountTypeAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data
        logger.error("ADD USER TYPE #####")
        logger.error(data)
        logger.error(request.user)
        logger.error(request.user.id)
        try:
            status = add_user_group(request.user,
                                    data.get('accType', '').lower())
            if status:
                result.update(status='success',
                              message='The account type was added successfully')
            else:
                result.update(status='error',
                              message='The account type is not added.')
        except Exception as exc:
            logger.error("AddUserAccountTypeAPIView:", exc)
            result.update(status='error',
                          message='The account type is not added.')
        return Response(result)


class BusinessLogoDeleteAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        logo_id = data.get('logo_id', '')

        try:
            response_data = remove_business_logo(user_id, logo_id)
            result.update(status='success' if response_data['is_success'] else 'error',
                          message=response_data['message'] if 'message' in response_data else '')
        except Exception as exc:
            logger.error("BusinesslogoDeleteAPIView:", exc)
            result.update(status='error',
                          message='The logo is not deleted.')
        return Response(result)


class ProfileImageDeleteAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        image_id = data.get('image_id', '')
        image_type = data.get('image_type', '')

        try:
            response_data = remove_profile_image(user_id, image_type, image_id)
            result.update(status='success' if response_data['is_success'] else 'error',
                          message=response_data['message'] if 'message' in response_data else '')
        except Exception as exc:
            logger.error("ProfileImageDeleteAPIView:", exc)
            result.update(status='error',
                          message='The image is not deleted!')
        return Response(result)


def get_profile_user_type(user):
    result = {}
    try:
        is_business = is_user_business(user)
        result['is_business'] = is_business
    except Exception as exc:
        is_business = False
        result['is_business'] = False
    try:
        is_general = is_user_general(user)
        result['is_general'] = is_general
    except:
        is_general = False
        result['is_general'] = False
    return result


class ProfileAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated, )

    def get(self, request):
        message = ""
        result = {'status': '',
                  'message': ''}
        data = request.query_params.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        user = get_object_or_None(User, id=user_id)
        business_type_choices = []
        context = {}

        profile_user_type_result = get_profile_user_type(user)
        is_business = profile_user_type_result['is_business']
        is_general = profile_user_type_result['is_general']
        context.update(profile_user_type_result)

        try:
            if is_business:
                card_invoices = Invoice.objects.filter(
                    user=user, type='CreditCard', is_deleted=False)
                card_serializer = PaymentMethodCardSerializer(
                    card_invoices, many=True)
                context['payment_card'] = card_serializer.data
                paypal_invoices = Invoice.objects.filter(
                    user=user, type='PayPalAccount', is_deleted=False)
                paypal_serializer = PaymentMethodPaypalSerializer(
                    paypal_invoices, many=True)
                context['payment_paypal'] = paypal_serializer.data
                profile = user.profile
                profile_completed = profile.is_completed
                if not profile_completed['status']:
                    message = profile_completed['message']

                for i in Profile.BUSINESS_TYPE_CHOICES:
                    business_type_choices.append({'code': i[0],
                                                  'name': i[1]})

                profile_serializer = ProfileBusinessSerializer(user.profile)

                profile_url, created = ProfileUrl.objects.get_or_create(
                    user=user)
                profile_urls = get_company_urls(profile_url)
                context.update(company_links=profile_urls,
                               business_types=business_type_choices)

            elif user.is_superuser or (user.is_staff and is_general) or is_general:
                profile_serializer = ProfileSerializer(user.profile)
            else:
                profile_serializer = ProfileSerializer(user.profile)

            logos = user.profile.logo_img.filter(is_deleted=False)
            business_logo_serializer = BusinessLogoSerializer(logos, many=True)

            extra_profile_images = user.profile.extra_profile_img.all()
            extra_profile_images_serializer = ExtraProfileImageSerializer(
                extra_profile_images, many=True)

            context.update(profile=profile_serializer.data,
                           business_logos=business_logo_serializer.data,
                           extra_profile_images=extra_profile_images_serializer.data)
            response_data = get_profile_detail(
                user_id, request.user.username, api_request=True, my_profile=True)

            status = 'success' if response_data.get(
                'status', '') != 'error' else 'error'
            message = response_data.get('message', '')
            if 'status' in response_data:
                response_data.pop('status')
            if 'message' in response_data:
                response_data.pop('message')
            response_data.update(context)
            result.update(status=status,
                          message=message,
                          data=response_data)
        except Exception as exc:
            logger.error("The My profile is not loaded: ", str(exc))
            result.update(status='error',
                          message="We're sorry. Your profile failed to load. Please try again later.")

        return Response(result)

    def post(self, request):
        context = {}
        message = ""
        is_success = True
        result = {'status': ''}
        data = request.data.copy()
        logger.info("PROFILE API data: %s", data)
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        user = get_object_or_None(User, id=user_id)

        profile_user_type_result = get_profile_user_type(user)
        is_business = profile_user_type_result['is_business']
        is_general = profile_user_type_result['is_general']
        context.update(profile_user_type_result)
        user_profile = user.profile
        incentive_amount = user_profile.incetive_val

        try:
            form1 = UserApiForm(data, instance=user)

            if is_business:
                form2 = BusinessUserProfileApiForm(
                    data, request.FILES, instance=user.profile)
                disc1 = data.get('disc1', None)
                url1 = data.get('url1', None)
                disc2 = data.get('disc2', None)
                url2 = data.get('url2', None)
                disc3 = data.get('disc3', None)
                url3 = data.get('url3', None)
                disc4 = data.get('disc4', None)
                url4 = data.get('url4', None)
                disc5 = data.get('disc5', None)
                url5 = data.get('url5', None)
                profile_url_checker = check_profile_urls(
                    url1, url2, url3, url4, url5)
                if profile_url_checker['status'] == 'error':
                    return Response(profile_url_checker)
            elif user.is_superuser or (user.is_staff and is_general) or is_general:
                form2 = ProfileApiForm(
                    data, request.FILES, instance=user.profile)

            if form1.is_valid() and form2.is_valid():
                form1.save()
                form2.save()
                if is_business:
                    profile_url = ProfileUrl.objects.get_or_create(user=user)
                    profile_url = profile_url[0]
                    profile_url.disc1 = disc1
                    profile_url.url1 = url1
                    profile_url.disc2 = disc2
                    profile_url.url2 = url2
                    profile_url.disc3 = disc3
                    profile_url.url3 = url3
                    profile_url.disc4 = disc4
                    profile_url.url4 = url4
                    profile_url.disc5 = disc5
                    profile_url.url5 = url5
                    profile_url.save()
                    # result = create_customer(request, '789', '4012888888881881', '10/2017')
                    if form2.cleaned_data['incetive_val'] != incentive_amount:
                        update_donate_unpaid_invoices(user)

                if Profile.objects.filter(user=user.id, email_sent=False).exists():
                    Profile.objects.filter(
                        user=user.id).update(email_sent=True)
                    confirm_path = '/admin/auth/user/%s/' % user.id

                    confirm = request.build_absolute_uri(confirm_path)

                    EmailTemplate.send(
                        template_key="account_verification_task_admin",
                        emails=settings.EMAIL_HOST_USER,
                        context={
                            "confirm_link": confirm,
                            "username": user.username
                        }
                    )
                message = "The profile was updated successfully!"
            else:
                is_success = False
                errors = form1.errors or form2.errors
                error = errors.popitem()
                label = error[0]
                if label in form1.fields:
                    label = form1.fields[label].label
                elif error[0] in form2.fields:
                    label = form2.fields[label].label
                message = "{} - {}".format(label, error[1][0])
        except Exception as exc:
            logger.error("Profile API is not updated: %s", exc)
            is_success = False
            message = "We're sorry. Your profile failed to load. Please try again later."
        status = "success" if is_success else 'error'
        result.update(status=status,
                      message=message)
        return Response(result)


class ProfileViewSet(viewsets.ViewSet):
    """
    API endpoint that validates user profile.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)


class ProfileBusinessViewSet(viewsets.ViewSet):
    """
    API endpoint that validates user business profile.
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileBusinessSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)


class ProfileNotificationViewSet(viewsets.ViewSet):
    """
    API endpoint that validates user profile notifications.
    """
    permission_classes = (CustomIsAuthenticated,)
    serializer_class = ProfileNotificationSerializer

    def retrieve(self, request, pk=None):
        '''

        :param request:
        :param pk: User Id
        :return: Serialized data of the notification data!
        '''

        result = {'status': '',
                  'message': ''}
        profile = get_object_or_None(Profile, user__id=pk)
        serializer = self.serializer_class(profile)
        data = serializer.data
        for k, v in data.items():
            value = 1 if v else 0
            data.update({k: value})
        if profile:
            result.update(status='success',
                          message='',
                          data=data)
        else:
            result.update(status='error',
                          message='User is not found')

        return Response(result)

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        success_message = 'Notification settings were updated successfully!'
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        profile = get_object_or_None(Profile, user__id=user_id)
        if profile:
            serializer = self.serializer_class(instance=profile,
                                               data=request.data)
            if serializer.is_valid():
                serializer.save()
                result.update(status='success',
                              message=success_message)
            else:
                errors = serializer.errors
                for k, v in errors.items():
                    result.update(status='error',
                                  message="{0} - {1}".format(k, v[0]))
                    break
        else:
            result.update(status='error',
                          message='User is not found')
        return Response(result)


class LoginAPIViewSet(viewsets.ViewSet):
    serializer_class = LoginSerializer

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        username = data['username']
        password = data['password']
        deviceToken = data['deviceToken']
        deviceType = data['deviceType']
        serializer = LoginSerializer(data=data)

        if serializer.is_valid():
            user = get_user(username, password)

            if user is not None:
                if user.is_active:
                    # create or activate fcm device token
                    devices = FCMDevice.objects.filter(
                        user=user, registration_id=deviceToken, type=deviceType)
                    if not devices.exists():
                        device = FCMDevice()
                        device.registration_id = deviceToken
                        device.type = deviceType
                        device.user = user
                    else:
                        device = devices.first()

                    if user.profile.two_fa_by_app:
                        device.active = True
                    else:
                        device.active = False

                    device.save()

                    # subscribe to top only first time when the token
                    if not devices.exists():
                        device.handle_topic_subscription(True, "OTP")
                    profile = user.profile
                    if profile.two_fa_by_email or profile.two_fa_by_app:
                        sendTwoFaNotification(user)

                        result.update(status='success',
                                      message='Enter code sent to you by email and/or mobile app notification',
                                      )
                    else:
                        login(request, user)
                        login_response_serializer = LoginResponseSerializer(
                            user)
                        result.update(status='success',
                                      message='Your login was successful!',
                                      data=login_response_serializer.data)
                else:
                    result.update(status='error',
                                  message='Your account has been deactivated. Email accounts@skigit.com to reactivate.')
            else:
                result.update(status='error',
                              message='Your username and/or password are incorrect. Please try again.')
        else:
            errors = serializer.errors
            for k, v in errors.items():
                result.update(status='error',
                              message="{0} - {1}".format(k, v[0]))
                break
        return Response(result)


def validateTwoFaCode(user, code):
    is_valid = timezone.now(
    ) <= user.profile.two_fa_code_expire_at and user.profile.two_fa_code == code
    if is_valid:
        user.two_fa_code = None
        user.two_fa_retry = 0
        user.save()
    return is_valid


class ValidateTwoFaViewset(viewsets.ViewSet):
    serializer_class = TwoFaSerializer

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        username = data['username']
        two_fa_code = data['two_fa_code']
        serializer = TwoFaSerializer(data=data)

        if serializer.is_valid():
            user = User.objects.filter(email=username)
            if user.exists():
                user = user.first()
                if validateTwoFaCode(user, two_fa_code):
                    login_response_serializer = LoginResponseSerializer(user)
                    result.update(status='success',
                                  message='Your login was successful!',
                                  data=login_response_serializer.data)
                else:
                    result.update(status='error',
                                  message='Incorrect code. Please try again.')
            else:
                result.update(status='error',
                              message='Username is incorrect. Please try again.')
        else:
            errors = serializer.errors
            for k, v in errors.items():
                result.update(status='error',
                              message="{0} - {1}".format(k, v[0]))
                break
        return Response(result)


class RsendTwoFaViewset(viewsets.ViewSet):
    serializer_class = EmailSerializer

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        username = data['username']
        serializer = EmailSerializer(data=data)

        if serializer.is_valid():
            user = User.objects.filter(email=username)
            if user.exists():
                user = user.first()
                profile = user.profile
                if profile.two_fa_retry > 0 and profile.two_fa_retry < 3:
                    sendTwoFaNotification(user, profile.two_fa_retry + 1)
                    result.update(status='success',
                                  message='Code has been resent')
                else:
                    result.update(status='error',
                                  message="You've reached the maximum resend limit.")
            else:
                result.update(status='error',
                              message='Username is incorrect. Please try again.')
        else:
            errors = serializer.errors
            for k, v in errors.items():
                result.update(status='error',
                              message="{0} - {1}".format(k, v[0]))
                break
        return Response(result)


def get_user(username,
             password):
    '''
    :param username:
    :param password:
    :return user object if it exists!
    '''

    users = User.objects.filter(email__iexact=username)

    if users.exists():
        user_name = users.last().username
        user = authenticate(username=user_name,
                            password=password)
    else:
        user = None
    return user


class PasswordResetEmailViewSet(viewsets.ViewSet):
    '''
    Check the email if it exists or not!
    '''
    serializer_class = PasswordResetEmailSerializer

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data
        DOMAIN_NAME = 'Skigit'
        email_template_name = 'registration/password_reset_email.html'
        form_class = PasswordResetForm
        from_email = settings.DEFAULT_FROM_EMAIL
        html_email_template_name = 'registration/password_reset_email.html'
        subject_template_name = 'registration/recovery_email_subject.txt'
        template_name = 'registration/password_reset_form.html'
        title = _('Password reset')
        token_generator = default_token_generator
        extra_email_context = {'title': title}

        email = data['email']
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            is_success, message = check_email_exists(email)
            if is_success:
                message = 'A password reset link has been emailed to you. Click the link to' \
                    ' reset your Skigit password.'
                opts = {
                    'use_https': request.is_secure(),
                    'token_generator': token_generator,
                    'from_email': from_email,
                    'email_template_name': email_template_name,
                    'subject_template_name': subject_template_name,
                    'request': request,
                    'html_email_template_name': html_email_template_name,
                    'extra_email_context': extra_email_context,
                    'domain_override': DOMAIN_NAME,
                    'domain': settings.MOBILE_HOST
                }
                form = PasswordResetForm(data)
                if form.is_valid():
                    form.save(**opts)
                    result.update(status='success',
                                  message=message)
            else:
                result.update(status='error',
                              message=message)
        else:
            errors = serializer.errors
            for k, v in errors.items():
                result.update(status='error',
                              message="{0} - {1}".format(k, v[0]))
                break
        return Response(result)


class UserAccountDeleteViewSet(viewsets.ViewSet):
    '''
    Check the email if it exists or not!
    '''
    permission_classes = (CustomIsAuthenticated,)
    #serializer_class = UserAccountDeleteSerializer

    def create(self, request):
        result = {'status': '',
                  'message': ''}
        success_message = 'Your account was deactivated successfully!'
        no_user_message = 'User is not found'
        user = request.user if request.auth else None

        if user:
            if not user_invoices_cleared(user):
                result.update(status='error',
                              message="Please clear pending invoice(s) before deactivating your account")
            else:
                delete_user_account(user)
                result.update(status='success',
                              message=success_message)
        else:
            result.update(status='error',
                          message=no_user_message)
        return Response(result)


class MyStatisticsAPIView(views.APIView):
    '''
    My Statistics REST View!
    '''

    permission_classes = (CustomIsAuthenticated,)

    def get(self, request, pk):
        '''

        :param request:
        :param pk: User Id
        :return: the statistics of the user
        '''
        result = {'status': '',
                  'message': ''}
        no_user_message = 'User is not found'
        data = request.query_params
        user = request.user
        if user:
            statistics = get_user_statistics(user)
            result.update(status='success',
                          message='',
                          data=statistics)
        else:
            result.update(status='error',
                          message=no_user_message)
        return Response(result)


class BusinessUserListAPIView(generics.ListAPIView):
    '''
    My Business List REST View!
    '''
    permission_classes = (CustomIsAuthenticated,)
    serializer_class = BusinessProfileDetailSerializer

    def list(self, request):
        '''

        :param request:
        :return: the business user
        '''
        result = {'status': '',
                  'message': ''}

        business_user = User.objects.filter(groups__name=settings.BUSINESS_USER,
                                            invoice_user__type__in=[
                                                'PayPalAccount', 'CreditCard'],
                                            invoice_user__is_deleted=False
                                            ).distinct('username')

        business_profile = Profile.objects.filter(user__id__in=business_user.values_list('id', flat=True),
                                                  payment_method__isnull=False,
                                                  payment_email__isnull=False)

        if request.GET.get('company_title', None) is not None:
            business_profile = business_profile.filter(
                company_title__icontains=request.GET.get('company_title'))[:10]

            def sortingByCompany_title(x):
                l = x.company_title.lower()
                return l.index(request.GET.get('company_title').lower())
            business_profile = sorted(
                business_profile, key=sortingByCompany_title)

        duplicateCompanies = {}
        for i, profile in enumerate(business_profile):
            company_name = profile.company_title
            if profile.company_title in duplicateCompanies:
                duplicateCompanies[profile.company_title] += 1
                # add extension sequential number for same name duplicates
                company_name = "{} - {}".format(profile.company_title,
                                                duplicateCompanies[profile.company_title])
            else:
                duplicateCompanies[profile.company_title] = 1
                # check if duplicate exists
                count = 0
                for p in business_profile:
                    if p.company_title == profile.company_title:
                        count += 1

                if count > 1:
                    company_name = "{} - {}".format(profile.company_title,
                                                    duplicateCompanies[profile.company_title])

            business_profile[i].company_title = company_name
        try:
            serializer = self.get_serializer(business_profile, many=True)
            result.update(status='success',
                          message='',
                          data=serializer.data)
        except Exception as exc:
            result.update(status='error',
                          message='')
        return Response(result)


class ProfileDetailAPIView(views.APIView):
    '''
    Profile detail View!
    '''

    def get(self, request, username):
        '''
        :param request:
        :return: the business user
        '''
        result = {'status': '',
                  'message': ''}

        data = request.query_params.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)

        try:
            response_data = get_profile_detail(
                user_id, username, api_request=True)
            status = 'success' if response_data.get(
                'status', '') != 'error' else 'error'
            message = response_data.get('message', '')
            if 'status' in response_data:
                response_data.pop('status')
            if 'message' in response_data:
                response_data.pop('message')
            result.update(status=status,
                          message=message,
                          data=response_data)
        except Exception as exc:
            logger.error("Serializer: ProfileDetailAPIView:", exc)
            result.update(status='error',
                          message='')
        return Response(result)


def get_profile_detail(user_id, username, api_request=False, my_profile=False):
    result = {}
    cur_user = get_object_or_None(User, id=user_id)

    try:
        request_user = get_object_or_None(
            User, username=username, is_active=True)
    except ObjectDoesNotExist:
        result.update(message="We’re sorry. This business account is no longer active on Skigit!",
                      redirect=reverse('home'),
                      status='error')
        return result

    if not my_profile and not request_user.profile.is_completed['status']:
        result.update(message="We’re sorry. This business account is no longer active on Skigit!",
                      status='error')
        return result

    business_logo = []
    like_dict = []
    friend_list = []
    ski_share_list = []
    company_url = None
    business_user = False

    if Profile.objects.filter(user=request_user).exists():
        request_user_profile = Profile.objects.get(user=request_user)
        extra_profile_img = request_user_profile.extra_profile_img.all()

        if api_request:
            extra_profile_img_url = [
                {'id': profile_img.id,
                 'profile_img': "{0}".format(api_request_images(profile_img.profile_img, quality=99, format='PNG'))}
                for profile_img in extra_profile_img]
        else:
            extra_profile_img_url = [
                {'id': profile_img.id,
                 # 'profile_img': "{0}".format(get_thumbnail(profile_img.profile_img, '300x120', quality=99, format='PNG').url)
                 'profile_img': "{0}".format(api_request_images(profile_img.profile_img, quality=99, format='PNG'))}
                for profile_img in extra_profile_img]

    if request_user.is_superuser or (
            request_user.is_staff and is_user_general(request_user)) or is_user_general(request_user):
        if not api_request:
            result['user_template'] = 'profile/general_user_profile.html'
    elif request_user.groups.all() and request_user.groups.all()[0].name == settings.BUSINESS_USER:
        business_user = True
        if not api_request:
            result['user_template'] = 'profile/business_user_profile.html'
    else:
        if not api_request:
            result.update(message='We’re sorry. This business account is no longer active on Skigit!',
                          redirect=reverse('home'),
                          status='error')
            return result

    if cur_user and cur_user.is_authenticated:
        if is_user_business(request_user):
            for bb_logo in request_user_profile.logo_img.filter(is_deleted=False).all():
                #bb_logo.img_id = bb_logo.id
                l_img = "{0}".format(api_request_images(
                    bb_logo.logo, quality=99, format='PNG'))
                # "{0}".format(get_thumbnail(bb_logo.logo, '300x120', quality=99, format='PNG').url
                #bb_logo.l_img = l_img
                business_logo.append({'id': bb_logo.id,
                                      'logo': l_img})
            company_url = ProfileUrl.objects.filter(
                user=request_user_profile.user)
            if api_request and company_url:
                company_url = get_company_urls(company_url[0])
                result.update({'company_links': company_url})
            else:
                result.update({'company_url': company_url})

        user_profile = Profile.objects.get(user=request_user)

        if Embed.objects.filter(to_user=request_user_profile.user,
                                is_embed=True).exists():
            embed_skigit_list = Embed.objects.filter(
                to_user=request_user_profile.user,
                is_embed=True).values_list('skigit_id', flat=True)

            if cur_user and cur_user.is_authenticated:
                if Friend.objects.filter(Q(to_user=cur_user.id) | Q(from_user=cur_user.id),
                                         status=1).exists():
                    f_list = Friend.objects.filter(Q(to_user=cur_user.id) | Q(from_user=cur_user.id),
                                                   status=1)
                    from_user_list = f_list.exclude(from_user=cur_user.id).values_list('from_user',
                                                                                       flat=True).distinct()
                    to_user_list = f_list.exclude(to_user=cur_user.id).values_list('to_user',
                                                                                   flat=True).distinct()
                    fr_list = list(merge(from_user_list, to_user_list))
                    friends_detail = Profile.objects.filter(
                        user__id__in=fr_list).order_by('user__username')
                    for friends in friends_detail:
                        if friends.profile_img:
                            #l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                            l_img = api_request_images(
                                friends.profile_img, quality=99, format='PNG')
                        else:
                            l_img = "{0}{1}".format(
                                settings.STATIC_URL, 'skigit/detube/images/noimage_user.jpg')
                        friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                            'name': friends.user.get_full_name(), 'image': "{0}".format(l_img)})
                video_likes = Like.objects.filter(
                    user_id=cur_user.id, status=True)
                for likes in video_likes:
                    like_dict.append(likes.skigit_id)
            vid = VideoDetail.objects.select_related('skigit_id').filter(skigit_id__id__in=embed_skigit_list,
                                                                         status=1)
            serializer = VideoDetailSerializer(vid, many=True)
            for vid_data in vid:
                sharObj = Share.objects.filter(skigit_id=vid_data,
                                               is_active=True,
                                               user=request_user_profile.user).order_by(
                    'to_user', '-pk').distinct('to_user')
                for sh in sharObj:
                    ski_share_list.append(
                        {'share_date': sh.created_date, 'username': sh.to_user.username,
                         'vid': sh.skigit_id_id})
            result.update({'video_detail': serializer.data,
                           'video_likes': like_dict,
                           'friend_list': friend_list,
                           'order_value': '1',
                           'togal_val': '1',
                           'skigit_list': ski_share_list,
                           'users': get_all_logged_in_users(),
                           'business_logos': business_logo})

    if business_user:
        profile_serializer = ProfileBusinessSerializer(request_user_profile)
    else:
        profile_serializer = ProfileSerializer(request_user_profile)
    profile_data = profile_serializer.data

    if 'profile_img' in profile_data and profile_data['profile_img']:
        profile_data['profile_img'] = "{0}".format(
            api_request_images(profile_data['profile_img']))
    if 'coupan_image' in profile_data and profile_data['coupan_image']:
        profile_data['coupan_image'] = "{0}".format(
            api_request_images(profile_data['coupan_image']))
    result.update({
        'extra_profile_images': extra_profile_img_url,
        'business_logos': business_logo,
        'request_user_profile': profile_data
    })
    return result


class GetSperkAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request, sperk_user_id):
        result = {'status': '',
                  'message': ''}
        data = request.query_params.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)

        try:
            if user_id:
                response = manage_sperk(sperk_user_id, api_request=True)
                result.update(status='success',
                              message='',
                              data=response)
            else:
                result.update(status='error',
                              message='Please login!')
        except Exception as exc:
            logger.error("Serializer: GetSperkAPIView:", exc)
            result.update(status='error',
                          message='The Sperk is not retrieved. Please try again later.')
        return Response(result)


class SperkDetailAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request, sperk_user_id):
        result = {'status': '',
                  'message': ''}
        data = request.query_params.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)

        try:
            if user_id:
                response_data = get_sperk_profile_detail(
                    user_id, sperk_user_id)
                status = 'success' if 'is_success' in response_data and response_data[
                    'is_success'] else 'error'
                message = response_data['message'] if 'message' in response_data and response_data['message'] else ''
                result.update(status=status,
                              message=message,
                              data=response_data['context'])
            else:
                result.update(status='error',
                              message='Please login!')
        except Exception as exc:
            logger.error("Serializer: SperkDetailAPIView:", exc)
            result.update(status='error',
                          message='The Sperk is not retrieved. Please try again later.')
        return Response(result)


class ChangePasswordAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data.copy()
        user_id = request.user.id if request.auth else 0
        data.update(user_id=user_id)
        form = PasswordChangeForm(
            user=get_object_or_None(User, id=user_id), data=data)

        try:
            if form.is_valid():
                form.save()
                result.update(status='success',
                              message='The password was changed successfully')
            else:
                errors = form.errors
                for i in errors.values():
                    result.update(message=i[0])
                    break
                result.update(status='error')
        except Exception as exc:
            logger.error("user views: ChangePasswordAPIView:", exc)
            result.update(status='error',
                          message='The password is not changed.')
        return Response(result)


class GeneralDataAPIView(views.APIView):

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        data = {}
        country_data = []
        language_data = []
        try:
            for code, name in countries:
                country_data.append({'code': code,
                                     'name': name})
            for code, name in Profile.LANGUAGE_CHOICES:
                language_data.append({'code': code,
                                      'name': name})
            data.update(countries=country_data,
                        languages=language_data)
            result.update(status="success",
                          message="",
                          data=data)
        except Exception as exc:
            logger.error("General Data throws error: ", exc)
            result.update(status='error',
                          message='Data is not loaded!')
        return Response(result)


class SperkListAPIView(generics.ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = SperkListSerializer
    permission_classes = (CustomIsAuthenticated,)
    pagination_class = PageNumberPagination

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        try:
            request_data = request.query_params
            sperks = Profile.objects.filter(
                business_verified=True).order_by('company_title')
            company_title = request.GET.get('company_title', None)
            if company_title is not None and company_title != '':
                sperks = sperks.filter(company_title__icontains=company_title)

                def sortingByCompany_title(x):
                    l = x.company_title.lower()
                    return l.index(company_title.lower())

                sperks = sorted(sperks, key=sortingByCompany_title)

            sperks = [sperk for sperk in sperks if sperk.is_completed['status']]
            page = self.paginate_queryset(sperks)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_result = self.get_paginated_response(serializer.data)
                data = paginated_result.data
            else:
                serializer = self.get_serializer(sperks, many=True)
                data = serializer.data
            result.update(status='success',
                          message='',
                          data=data)
        except Exception as exc:
            logger.error("Serializer: SperkListAPIView:", exc)
            result.update(status='error',
                          message='Sperks are empty.')
        return Response(result)


class VideoPluggedAPIView(generics.ListAPIView):
    queryset = VideoDetail.objects.all()
    serializer_class = VideoDetailSerializer
    pagination_class = PageNumberPagination
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request, user_id):
        result = {'status': '',
                  'message': ''}
        try:
            user_id = request.user.id if request.auth else 0
            videos = get_user_plugged_videos(user_id)
            page = self.paginate_queryset(videos)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_result = self.get_paginated_response(serializer.data)
                data = paginated_result.data
            else:
                serializer = self.get_serializer(videos, many=True)
                data = serializer.data
            result.update(status='success',
                          message='',
                          data=data)
        except Exception as exc:
            logger.error("Serializer: VideoPluggedAPIView:", exc)
            result.update(status='error',
                          message='There is an issue while loading skigits. Please try again.')
        return Response(result)


class VideoFollowAPIView(generics.ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileFriendSerializer
    pagination_class = PageNumberPagination
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request, user_id):
        result = {'status': '',
                  'message': ''}
        try:
            user_id = request.user.id if request.auth else 0
            followers = get_followers(user_id)
            page = self.paginate_queryset(followers)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_result = self.get_paginated_response(serializer.data)
                data = paginated_result.data
            else:
                serializer = self.get_serializer(followers, many=True)
                data = serializer.data
            result.update(status='success',
                          message='',
                          data=data)
        except Exception as exc:
            logger.error("Serializer: VideoFollowersAPIView:", exc)
            result.update(status='error',
                          message='There is an issue while loading followers. Please login and try again.')
        return Response(result)


class SocialnetworkRegisterAPIView(views.APIView):

    def post(self, request):
        result = {'status': '',
                  'message': ''}
        data = request.data
        provider = data.get('provider', '')

        try:
            id = data.get('id', '')
            name = data.get('name', '')
            username = data.get('username', '')
            profile_image_url = data.get('profile_image_url', '')
            email = data.get('email', '')

            if provider == 'facebook':
                pass
        except Exception as exc:
            logger.error("API: SocialnetworkRegisterAPIView:", exc)
            result.update(status='error',
                          message='The register is not successful. Please try again.')
        return Response(result)


class PaymentGatewayTokenAPIView(views.APIView):
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request):
        result = {'status': '',
                  'message': ''}
        try:
            user = request.user if request.auth else None
            cc_token = client_token(request="", user=user)
            pay_pal_token = client_paypal_token(request="", user=user)
            result.update(status='success',
                          data={'card_token': cc_token,
                                'pay_pal_token': pay_pal_token})
        except Exception as exc:
            logger.error("Payment gateway token API:", exc)
            result.update(status='error',
                          message='The payment gateway token is not created.')
        return Response(result)


class FacebookLoginAPI(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter

    def post(self, request, *args, **kwargs):
        result = {'status': 'error',
                  'message': 'Your login is not successful!'}
        try:
            self.request = request
            self.serializer = self.get_serializer(data=self.request.data,
                                                  context={'request': request})
            self.serializer.is_valid(raise_exception=True)

            self.login()
            response_data = self.get_response()
            if response_data.status_code == 200:
                login_response_serializer = LoginResponseSerializer(self.user)
                result.update(status='success',
                              message='Your login was successful!',
                              data=login_response_serializer.data)
        except Exception as exc:
            if 'User is already registered with this e-mail address.' in str(exc):
                result['message'] = 'Your email address is already registered with Skigit.com. Please Sign in with that email'
            logger.error("Facebook rest auth Login API Failed:", exc)
        return Response(result)


class CustomTwitterOAuthAdapter(TwitterOAuthAdapter):
    def complete_login(self, request, app, token, response):
        client = TwitterAPI(request, app.client_id, app.secret,
                            self.request_token_url)
        extra_data = client.get_user_info()

        # raise excpetion if email already exist
        if 'email' in extra_data and extra_data['email'] != '' and extra_data['email'] is not None:
            accounts = get_user_model().objects.filter(
                email=extra_data['email']
            )
            if accounts.exists():
                account = accounts.first()
                if not account.socialaccount_set.filter(provider='twitter').exists():
                    raise serializers.ValidationError(
                        _("User is already registered with this e-mail address.")
                    )
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)


class TwitterLoginAPI(SocialLoginView):
    serializer_class = TwitterLoginSerializer
    adapter_class = CustomTwitterOAuthAdapter

    def post(self, request, *args, **kwargs):
        result = {'status': 'error',
                  'message': 'Your login is not successful!'}
        try:
            self.request = request
            self.serializer = self.get_serializer(data=self.request.data,
                                                  context={'request': request})
            self.serializer.is_valid(raise_exception=True)

            self.login()
            response_data = self.get_response()
            if response_data.status_code == 200:
                login_response_serializer = LoginResponseSerializer(self.user)
                result.update(status='success',
                              message='Your login was successful!',
                              data=login_response_serializer.data)
        except Exception as exc:
            if 'User is already registered with this e-mail address.' in str(exc):
                result['message'] = 'Your email address is already registered with Skigit.com. Please Sign in with that email'
            logger.error("Twitter rest auth Login API Failed:", exc)
        return Response(result)


class InstagramLoginAPI(SocialLoginView):
    adapter_class = InstagramOAuth2Adapter

    def post(self, request, *args, **kwargs):
        result = {'status': 'error',
                  'message': 'Your login is not successful!'}
        try:
            self.request = request

            _mutable = request.data._mutable

            request.data._mutable = True

            request.data.update({"access_token": generateTokenFromCode(
                'instagram', self.request.data['access_token'])})

            request.data._mutable = _mutable

            self.serializer = self.get_serializer(data=self.request.data,
                                                  context={'request': request})
            self.serializer.is_valid(raise_exception=True)

            self.login()
            response_data = self.get_response()
            if response_data.status_code == 200:
                login_response_serializer = LoginResponseSerializer(self.user)
                result.update(status='success',
                              message='Your login was successful!',
                              data=login_response_serializer.data)
        except Exception as exc:
            if 'User is already registered with this e-mail address.' in str(exc):
                result['message'] = 'Your email address is already registered with Skigit.com. Please Sign in with that email'
            logger.error("Instagram rest auth Login API Failed:", exc)
        return Response(result)


class LinkedinLoginAPI(SocialLoginView):
    adapter_class = LinkedInOAuth2Adapter

    def post(self, request, *args, **kwargs):
        result = {'status': 'error',
                  'message': 'Your login is not successful!'}
        try:
            self.request = request
            self.serializer = self.get_serializer(data=self.request.data,
                                                  context={'request': request})
            self.serializer.is_valid(raise_exception=True)

            self.login()
            response_data = self.get_response()
            if response_data.status_code == 200:
                login_response_serializer = LoginResponseSerializer(self.user)
                result.update(status='success',
                              message='Your login was successful!',
                              data=login_response_serializer.data)
        except Exception as exc:
            if 'User is already registered with this e-mail address.' in str(exc):
                result['message'] = 'Your email address is already registered with Skigit.com. Please Sign in with that email'
            logger.error("LinkedIn rest auth Login API Failed:", exc)
        return Response(result)


class CustomPasswordChangeView(PasswordChangeView):
    twoFactorForm = TwoFactorAuthForm
    '''
		Custom password change. Save new password and send the email
	'''

    def get_context_data(self, **kwargs):
        context = super(PasswordChangeView, self).get_context_data(**kwargs)
        context['two_factor_form'] = TwoFactorAuthForm(user=self.request.user)
        context['everyone_allowance'] = self.request.user.profile.everyone_allowance

        return context

    def form_valid(self, form):
        super().form_valid(form)
        notify_password_change(self.request.user.email)
        return HttpResponseRedirect(self.success_url)


class RegisterConfirmAPIView(views.APIView):

    def get(self, request, activation_key):
        result = {'status': '',
                  'message': ''}
        response = register_confirm(activation_key)
        result.update(status=response['status'],
                      message=response['message'])
        return Response(result)


class UpdateTwoFaAPIView(views.APIView):

    def post(self, request):
        field = request.data.get('field')
        value = request.data.get('value')
        return Response(updateTwoFaSettings(request, field, value))


class LogoutAPIView(views.APIView):

    def post(self, request):
        result = {}
        try:
            data = request.data.copy()
            deviceToken = data['deviceToken']
            deviceType = data['deviceType']
            serializer = BaseAPISerialier(data=data)
            if not request.user.is_authenticated:
                result.update(status="error", message="Invalid token")

            if serializer.is_valid():
                device = FCMDevice.objects.filter(
                    user=request.user, registration_id=deviceToken, type=deviceType)
                if device.exists():
                    device = device.first()
                    device.active = False
                    device.save()

                request.user.auth_token.delete()
                result.update(status="success",
                              message="Successfully logged out")
            else:
                errors = serializer.errors
                for k, v in errors.items():
                    result.update(status='error',
                                  message="{0} - {1}".format(k, v[0]))
                    break
        except Exception as exc:
            logger.error("Logout API Error :", exc)
            result.update(status="error",
                          message="Error occurred. Contact administrator")
        return Response(result)


def updateTwoFa(request):
    field = request.POST.get('field')
    value = json.loads(request.POST.get('value', 'false'))

    return JsonResponse(updateTwoFaSettings(request, field, value))


def updateAllowance(request):
    allowance = request.POST.get('allowance')
    profile = request.user.profile
    profile.everyone_allowance = ast.literal_eval(allowance)
    profile.save()
    return JsonResponse({'success': True})


def updateTwoFaSettings(request, field, value):
    allowed_fields = ['two_fa_by_app', 'two_fa_by_email']

    if request.user.is_authenticated and field in allowed_fields:
        profile = request.user.profile
        setattr(profile, field, value)
        profile.save()

        message = "Two factor authentication settings have been updated for Email Authentication"
        if field == "two_fa_by_app":
          message = "Two factor authentication settings have been updated for Mobile App Authentication"

        return {
            "message": message,
            "status": "success",
            "success": True,
        }
    return {
        "message": "Error occurred. Please contact with administrator",
        "status": "error",
        "success": False,
    }


def validateTwoFa(request):
    email = request.POST.get('email')
    twoFaCode = request.POST.get('code')

    user = User.objects.filter(email=email)
    if user.exists() and validateTwoFaCode(user.first(), twoFaCode):
        login(request, user.first(),
              backend='django.contrib.auth.backends.ModelBackend')

        return JsonResponse({
            'message': 'Your login was successful!',
            "success": True,
        })
    return JsonResponse({
        "message": "Incorrect code",
        "success": False,
    })


def resendTwoFa(request):
    email = request.POST.get('email')

    user = User.objects.filter(email=email)
    if user.exists():
        user = user.first()
        profile = user.profile
        if profile.two_fa_retry > 0 and profile.two_fa_retry < 3:
            sendTwoFaNotification(user, user.profile.two_fa_retry + 1)
            return JsonResponse({
                'message': 'Code has been resent',
                "success": True,
            })
        else:
            return JsonResponse({
                'message': "You've reached the maximum resend limit.",
                "success": False,
            })
    else:
        return JsonResponse({
            'message': 'Username is incorrect',
            "success": False,
        })


@method_decorator(login_required(login_url='/login'), name='dispatch')
@method_decorator(require_admin, name='dispatch')
class VerifyAccountAPIView(views.APIView):
    def post(self, request):
        try:
            user = User.objects.get(id=request.POST['user_id'])
            profile = Profile.objects.get(user=user)
            profile.business_verified = True
            profile.save()
            # activate skigits of this user
            Video.objects.filter(user=user).update(is_active=True)

            EmailTemplate.send(
                template_key="account_verification_admin",
                emails=profile.contact_email,
                context={
                    "username": request.user.username,
                    "host": ''.join(settings.HOST)
                }
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed'})


@method_decorator(login_required(login_url='/login'), name='dispatch')
@method_decorator(require_admin, name='dispatch')
class RejectAccountAPIView(views.APIView):
    def post(self, request):
        try:
            user = User.objects.get(id=request.POST['user_id'])
            profile = Profile.objects.get(user=user)
            profile.business_verified = False
            profile.save()

            # deactivate skigits of this user
            Video.objects.filter(user=user).update(is_active=False)

            EmailTemplate.send(
                template_key="account_rejection_admin",
                emails=profile.contact_email,
                context={
                    "reason": request.POST['reason'],
                    "host": ''.join(settings.HOST)
                }
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed'})
