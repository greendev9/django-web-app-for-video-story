"""skigit_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

import notifications.urls
from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import PasswordChangeDoneView
from django.views.generic.base import TemplateView, RedirectView
from django.views.static import serve as view_static_server
from rest_framework import routers, renderers


from core.views import (index, SkigitBaseView, Home, CategoryAPIView, SubjectCategoryAPIView,
                        ShareManageDeeplinkView, UrlExistView, UrlListAPIView, skigit_friend_invite,
                        AdminDataMigrateAPIView, AdminDataMigrateUpdateAPIView, sendOtpAPIView,
                        verifyOtpAPIView,isPhoneValidAPIView)
from user.socialauth import social_login_type
from friends.views import (brochure_preview, wall_poster_preview, ProfileFriendsInviteAPIView,
                           FriendInviteInternalAPIView, FriendInviteEmailAPIView, FriendRemoveAPIView,
                           FriendInviteNotificationsAPIView, GeneralNotificationsAPIView, NotificationCountAPIView,
                           DeleteNotificationAPIView, ReadNotificationAPIView, FriendAcceptAPIView)
from invoices.views import *
from invoices.reports import MyTemplateView, UnPaidCustomerView
from skigit.views import *
from sperks.views import Sperks
from user.views import *
from friends.views import SkigitInternalEmbedFeeAPIView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

import django_summernote
from fcm_django.api.rest_framework import FCMDeviceViewSet, FCMDeviceAuthorizedViewSet

admin.autodiscover()

router = routers.DefaultRouter()

router.register(r'account/register', RegisterViewSet, basename='Register')
router.register(r'account/login', LoginAPIViewSet, basename='Login')
router.register(r'account/validate-two-fa', ValidateTwoFaViewset, basename='validate-two-fa-api')
router.register(r'account/resend-two-fa', RsendTwoFaViewset, basename='resend-two-fa-api')
router.register(r'account/password/reset', PasswordResetEmailViewSet, basename='Forgot Password')
router.register(r'account/profile/notifications', ProfileNotificationViewSet, basename='Profile')
router.register(r'account/delete', UserAccountDeleteViewSet, basename='account-delete')
router.register(r'bug/report', BugReportViewSet, basename='bug-report')
router.register(r'devices', FCMDeviceViewSet)

about_us_patterns = [
    url(r'^$', SkigitBaseView.as_view(template_name='static/about_us.html'),
        name='aboust_us_view'),
    url(r'^faq/$', SkigitBaseView.as_view(template_name='static/faq.html'),
        name='faq_view'),
    url(r'^privacy-policy/$', SkigitBaseView.as_view(template_name='static/privacy_policy.html'),
        name='privacy_policy_view'),
    url(r'^terms-of-service/$', SkigitBaseView.as_view(template_name='static/t_and_c.html'),
        name='t_and_c_view'),
    url(r'^acceptable-use-policy/$', SkigitBaseView.as_view(template_name='static/acceptable_use_policy.html'),
        name='acceptable_use_policy_view'),
    url(r'^copyright-policy/$', SkigitBaseView.as_view(template_name='static/copyright_policy.html'),
        name='copyright_policy'),
    url(r'^skigit-for-business/$', SkigitBaseView.as_view(template_name='static/skigit_for_business.html'),
        name='skigit_for_business_view'),
    url(r'^business-verification/$', SkigitBaseView.as_view(template_name='static/business_verification.html'),
        name='business_verification'),
    url(r'^skigit-for-investors/$', SkigitBaseView.as_view(template_name='static/Investors.html'),
        name='skigit_for_investors_view'),
    url(r'^business-value-services-fees/$', SkigitBaseView.as_view(template_name='static/business_value_services_fees.html'),
        name='business_value_services_fees'),
    url(r'^rules-for-your-company-skigit/$',
        SkigitBaseView.as_view(template_name='static/rules_for_your_company_skigit.html'),
        name='rules_company_skigit'),
    url(r'^business-terms-of-service/$', SkigitBaseView.as_view(template_name='static/business_terms_of_service.html'),
        name='business_terms_service'),
]

guidelines_patterns = [
    url(r'^$', SkigitBaseView.as_view(template_name='static/guidelines.html'),
        name='guidelines_view'),
    url(r'^skigitology/$', SkigitBaseView.as_view(template_name='static/skigitology.html'),
        name='skigitology_view'),
    url(r'^skigit-length/$', SkigitBaseView.as_view(template_name='static/skigit_length.html'),
        name='skigit_length_view'),
    url(r'^making-your-skigit/$', SkigitBaseView.as_view(template_name='static/making_your_skigit_view.html'),
        name='making_your_skigit_view'),
    url(r'^allowed-video_formats/$', SkigitBaseView.as_view(template_name='static/allowed_video_formats_view.html'),
        name='allowed_video_formats_view'),
]

about_us_api_patterns = [
    url(r'^view/$', SkigitBaseView.as_view(template_name='static/about_us.html'),
        {'mobile_api_request': True}, name='about_us_view_api'),
    url(r'^faq/view/$', SkigitBaseView.as_view(template_name='static/faq.html'),
        {'mobile_api_request': True}, name='faq_view_api'),
    url(r'^privacy-policy/view/$', SkigitBaseView.as_view(template_name='static/privacy_policy.html'),
        {'mobile_api_request': True}, name='privacy_policy_view_api'),
    url(r'^terms-of-service/view/$', SkigitBaseView.as_view(template_name='static/t_and_c.html'),
        {'mobile_api_request': True}, name='t_and_c_view_api'),
    url(r'^acceptable-use-policy/view/$', SkigitBaseView.as_view(template_name='static/acceptable_use_policy.html'),
        {'mobile_api_request': True}, name='acceptable_use_policy_view_api'),
    url(r'^copyright-policy/view/$', SkigitBaseView.as_view(template_name='static/copyright_policy.html'),
        {'mobile_api_request': True}, name='copyright_policy_api'),
    url(r'^skigit-for-business/view/$', SkigitBaseView.as_view(template_name='static/skigit_for_business.html'),
        {'mobile_api_request': True}, name='skigit_for_business_view_api'),
    url(r'^business-verification/view/$', SkigitBaseView.as_view(template_name='static/business_verification.html'),
        {'mobile_api_request': True}, name='business_verification_api'),
    url(r'^skigit-for-investors/view/$', SkigitBaseView.as_view(template_name='static/Investors.html'),
        {'mobile_api_request': True}, name='skigit_for_investors_view_api'),
    url(r'^business-value-services-fees/view/$', SkigitBaseView.as_view(template_name='static/business_value_services_fees.html'),
        {'mobile_api_request': True}, name='business_value_services_fees_api'),
    url(r'^rules-for-your-company-skigit/view/$',
        SkigitBaseView.as_view(template_name='static/rules_for_your_company_skigit.html'),
        {'mobile_api_request': True}, name='rules_company_skigit_api'),
    url(r'^business-terms-of-service/view/$', SkigitBaseView.as_view(template_name='static/business_terms_of_service.html'),
        {'mobile_api_request': True}, name='business_terms_service_api'),
]

guidelines_api_patterns = [
    url(r'^view/$', SkigitBaseView.as_view(template_name='static/guidelines.html'),
        {'mobile_api_request': True}, name='guidelines_view_api'),
    url(r'^skigitology/view/$', SkigitBaseView.as_view(template_name='static/skigitology.html'),
        {'mobile_api_request': True}, name='skigitology_view_api'),
    url(r'^skigit-length/view/$', SkigitBaseView.as_view(template_name='static/skigit_length.html'),
        {'mobile_api_request': True}, name='skigit_length_view_api'),
    url(r'^making-your-skigit/view/$', SkigitBaseView.as_view(template_name='static/making_your_skigit_view.html'),
        {'mobile_api_request': True}, name='making_your_skigit_view_api'),
    url(r'^allowed-video_formats/view/$', SkigitBaseView.as_view(template_name='static/allowed_video_formats_view.html'),
        {'mobile_api_request': True}, name='allowed_video_formats_view_api'),
]


urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^accounts/login/$', RedirectView.as_view(url='/login/')),
    url(r'^accounts/', include('allauth.urls')),
    url('grappelli/', include('grappelli.urls')),
    url(r'^summernote/', include('django_summernote.urls')),
    #url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^verifyBusinessAccount/', VerifyAccountAPIView.as_view(), name='verify_account'),
    url(r'^rejectBusinessAccount/', RejectAccountAPIView.as_view(), name='reject_account'),
    url(r'^skigit-admin/report/', MyTemplateView.as_view(), name='teste_report'),
    url(r'^skigit-admin/unpaid/customer/', UnPaidCustomerView.as_view(), name='teste_report'),
    url(r'^$', Home.as_view(), name='index'),
    url(r'^skigit_friend_invite/$', skigit_friend_invite, name='skigit_friend_invite'),
    url(r'^landing-modal', TemplateView.as_view(template_name='beta_landing_page.html'), name='landing_modal'),
    url(r'^login/$', login_require, name='login_require'),
    url(r'^sitemap\.xml$', TemplateView.as_view(template_name='sitemap.xml', content_type='text/xml')),
    url(r'^friends/', include('friends.urls')),
    url(r'^invoice/', include('invoices.urls')),
    url(r'^api/v1/auth/login/$', LoginViewAPI.as_view(), name='login'),
    url(r'^login_ajax/$', LoginView.as_view(), name='login_ajax'),
    url(r'^register/$', RegisterType.as_view(), name='register_type'),
    url(r'^manage/register/type/$', ManageRegisterType.as_view(), name='manage-register-type'),
    url(r'^social-login/(?P<social_type>\w+)/', social_login_type, name='social_login'),
    url(r'^register/confirm/(?P<activation_key>\w+)/', RegisterConfirm.as_view(), name='register_confirm'),
    url(r'^reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/$',
        ResetConfirm.as_view(), name='password_reset_confirm'),
    url(r'^reset/done/$', SkigitBaseView.as_view(template_name='registration/password_reset_complete.html'),
        name='reset_done'),
    url(r'^reset/success/$', SkigitBaseView.as_view(template_name='registration/password_resets_done.html'),
        name='reset_success'),
    url(r'^reset/$', Reset.as_view(), name='reset'),
    url(r'^email_exits_check/$', email_exits_check, name='email_exits_check'),
    url(r'^check_social_user/$', check_social_user, name='check_social_user'),
    url(r'^logout/done/$', LogoutUser.as_view(), name='logout_user'),
    url(r'^logout/$', LogoutUser.as_view(), name='logout_page'),
    url(r'^update-two-fa/$', updateTwoFa, name='update_two_fa'),
    url(r'^update-allowance/$', updateAllowance, name='update_allowance'),
    url(r'^validate-two-fa/$', validateTwoFa, name='validate-two-fa'),
    url(r'^resend-two-fa/$', resendTwoFa, name='resend-two-fa'),

    url(r'about-us/', include((about_us_patterns,'core'), namespace="about_us_url")),
    url(r'guidelines/', include((guidelines_patterns,'core'), namespace="guidelines_url"), name="guidelines"),

    url(r'^category/(?P<cat_slug>[a-z]+)/sort-by-date/(?P<order_by>\d+)/$', sort_by_date,
        name='date_sort_view'),
    url(r'^category/(?P<cat_slug>[a-z]+)/sort-by-title/(?P<order_by>\d+)/$', sort_by_title,
        name='title_sort_view'),
    url(r'^category/(?P<cat_slug>[a-z]+)/sort-by-views/(?P<order_by>\d+)/$', sort_by_views,
        name='views_sort_view'),
    url(r'^category/(?P<cat_slug>[a-z]+)/sort-by-Likes/(?P<order_by>\d+)/$', sort_by_likes,
        name='like_sort_view'),
    url(r'^category/(?P<cat_slug>[a-z]+)/sort-by-random/$', sort_by_random, name='random_sort_view'),

    url(r'^category/(?P<cat_slug>[a-z]+)/', category_detail_view, name='category_detail_view'),
    url(r'^awesomethings/$', AwesomeThings.as_view(), name='awesome_things'),
    url(r'^awesomethings/(?P<sub_cat_slug>[\w.@+-]+).html', AwesomeThingsCategory.as_view(),
        name='awesome_things_category'),

    url(r'^skigit_data/(?P<pk>\d+)/$', SkigitData.as_view(), name='skigit_data'),
    url(r'^skigit_data/(?P<pk>\d+)/plugin-map-ajax/$', SkigitPluginMap.as_view(), name='skigit_plugin_map'),
    url(r'^skigit_data/(?P<videoId>\d+)/plugin-map/$', skigit_search_view, name='skigit_plugins'),
    url(r'^recommended_skigits/(?P<skigit_id>\d+)/$', recommended_skigits, name='recommended_skigits'),

    url(r'^sperk/$', Sperks.as_view(), name='sperks'),

    url(r'^sperk/(?P<user>\d+)/(?P<logo>\d+)/$', sperk_profile, name='sperk_profile'),

    url(r'^get-sperk/$', GetSperk.as_view(), name='get_sperk'),

    url(r'^profile/$', UserProfile.as_view(), name='user_profile'),

    # Plugin skigit
    url(r'^plugin/(?P<plug_id>[\w.@+-]+)/$', ajax_skigit_plugin_link, name='skigit_plugin'),
    url(r'^plugin-vid/(?P<plug_id>[\w.@+-]+)/$', ajax_skigit_plugin_video, name='skigit_plugin_video'),


    url(r'^view_count_update/$', skigit_count_update, name='view_count_update'),

    url(r'^upload/$', DirectUpload.as_view(), name="direct_upload"),
    url(r'^business-users/$', search_business_users, name="search_business_users"),
    # url(r'^youtube/direct-upload/$', DirectUpload.as_view(), name="youtube_direct_upload"),
    url(r'^youtube/link-upload/?$', LinkUpload.as_view(), name="youtube_link_upload"),
    url(r'^youtube/video-check/?$', YoutubeCheck.as_view(), name="youtube_check"),
    # url(r'^youtube/remove-profile-pic/?$', RemoveImages.as_view(), name="remove_profile_pic"),

    url(r'^profile/password_change/$', CustomPasswordChangeView.as_view(), {
        'post_change_redirect': '/profile/password_change/done/'
    }, name="password_change"),
    url(r'^profile/password_change/done/$', PasswordChangeDoneView.as_view(), name='password_change_done'),
    url(r'^profile/notifications/$', user_profile_notifications, name='user_profile_notifications'),
    url(r'^profile/deleteskigit/$', delete_skigit, name='delete_skigit'),
    url(r'^profile/delete/$', user_profile_delete, name='user_profile_delete'),
    url(r'^profile/my_statistics/$', my_statistics, name='my_statistics'),
    url(r'^profile/business_analytics/$', BusinessAnalytics.as_view(), name='business_analytics'),
    url(r'^profile/invoice/$', invoice_payment, name='user_payment_setup'),

    # user profile
    url(r'^profile/(?P<username>[\w.@+-]+)/$', UserProfileDisplay.as_view(), name='user_profile_display'),


    url(r'^get_notification_count/$', get_user_notification, name='get_notification_count'),

    url(r'^my-skigits/$', my_skigits, name='my_skigits'),
    url(r'^my-skigits/(?P<user_id>[\w.@+-]+)/$', my_skigits_view, name='my_skigits_view'),
    url(r'^plugged-in-skigits/$', plugged_in_skigits, name='plugged_in_skigits'),
    url(r'^unplug-skigit/$', unplug_skigit, name='unplug_skigit'),
    url(r'^like/$', liked_skigits, name='liked_skigits'),
    url(r'^favorite/$', favorite_skigits, name='favorite_skigits'),
    url(r'^following/$', i_am_following_view, name='i_am_following'),
    # follow skigit on popup page
    url(r'^follow/$', i_am_following, name='i_am_following'),
    url(r'^unfollow/$', un_following, name='i_am_following'),
    url(r'^skigit_statistics/$', skigit_statistics, name='statistics'),
    # skigit Like/Unlike
    url(r'^view_count_update/$', skigit_count_update, name='view_count_update'),
    url(r'^skigit_i_like/$', skigit_i_like, name='skigit_like'),
    url(r'^skigit_i_unlike/$', skigit_i_unlike, name='skigit_unlike'),
    # favourite/un-favourite Skigit
    url(r'^my_favourites/$', my_favourite_skigit, name='my_favourite_skigit'),
    url(r'^un_favourites/$', un_favourite_skigit, name='un_favourite_skigit'),
    # Skigit View count
    url(r'^skigit_view_count/$', skigit_view_count, name='skigit_view_count'),
    url(r'^search_skigit/$', skigit_search_view, name='skigit_search'),
    url(r'^search_skigit/(?P<order>[\w.@&+-]+)$', search_ordering_skigit,
        name='skigit_search_ordering'),
    # Inappropriate skigit
    url(r'^skigit_inapp_reason/$', skigit_inapp_reason, name='skigit_inapp_reason'),
    # social share redirect url
    url(r'^social_redirect/(?P<video_id>[\w.@+-]+)/$', social_redirect, name="social_redirect"),
    url(r'^share-skigits/$', share_to_friends, name="share_skigit_to_friends"),
    url(r'^email-share-skigit/$', email_share_friends, name="share_skigit_friends"),
    # To display logo in skgit popup_page form
    url(r'^display_business_logo/$', display_business_logo, name='display_business_logo'),
    url(r'^copyright-infringement/(?P<ski_id>\d+)/$', copyright, name='copyright_infringement'),
    # Get Embed Skigit
    url(r'^skigit-embed/(?P<video>[\w.@+-]+)/$', embed_skigit, name='embed_skigit'),
    url(r'^wall-poster-preview/$', wall_poster_preview, name='wall_poster_preview'),
    url(r'^brochure-preview/$', brochure_preview, name='brochure_preview'),

    url(r'^business_logo_upload_target/$', business_logo, name='business_logo'),
    url(r'^business_logo_get_target/$', business_logo_get_target, name='business_logo_get_target'),
    url(r'^delete_business_logo/$', delete_business_logo, name='delete_business_logo'),
    url(r'^business_doc_upload_target/$', business_doc, name='business_doc'),
    url(r'^business_doc_get_target/$', business_doc_get_target, name='business_doc_get_target'),
    url(r'^delete_business_doc/$', delete_business_doc, name='delete_business_doc'),
    url(r'^profile_get_target/$', profile_get_target, name='profile_get_target'),
    url(r'^profile_upload-target/$', profile_extra_image, name='profile_extra_image'),
    url(r'^delete_extra_profile_image/$', delete_extra_profile_image,
        name='delete_extra_profile_image'),
    url(r'^profile_pic/$', profile_pic, name='profile_pic'),
    url(r'^coupan_image_upload/$', coupan_image_upload, name='coupan_image_upload'),
    url(r'^check/url-exist/$', UrlExistView.as_view(), name='url-exist'),
    url(r'^check/video-title-exist/$', VideoTitleExistView.as_view(), name='video-title-exist'),

    url(r'^skigit/', include(('skigit.urls','core'), namespace="skigit")),

    url(r'^bug-management/$', bug_management, name='bug_management'),
    url(r'^share/(?P<pk>\d+)/$', Sharing.as_view(), name="share"),
    url(r'^social/register/delete/(?P<pk>\d+)/$', SocialRegisterDelete.as_view(), name="remove_social_register"),

    url(r'^api/v1/account/rest-auth/password/reset/confirm/$', CustomPasswordResetConfirmAPIView.as_view(),
        name='rest_password_reset_api_confirm'),

    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
    url(r'^get-states/$', get_state_list, name='get_state_list'),

    ## API REST Urls
    url(r'^api/v1/token/$', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    url(r'^api/v1/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    url(r'^api/v1/add/account-type/$', AddUserAccountTypeAPIView.as_view(), name='add-user-account-type'),
    url(r'api/v1/guidelines/', include((guidelines_api_patterns,'core'), namespace="guidelines_api_url"), name="guidelines-api"),
    url(r'api/v1/about-us/', include((about_us_api_patterns,'core'), namespace="aboutus_api_url"), name="aboutus-api"),
    url(r'^api/v1/general/data/$', GeneralDataAPIView.as_view(), name='general-data-api'),
    url(r'^api/v1/register/confirm/(?P<activation_key>\w+)/', RegisterConfirmAPIView.as_view(), name="register-confirm-api"),
    url(r'^api/v1/account/profile/$', ProfileAPIView.as_view(), name='account-api-profile'),
    url(r'^api/v1/account/image/upload/$', AccountImageUploadAPIView.as_view(), name='account-api-image-upload'),
    url(r'^api/v1/account/image/delete/$', ProfileImageDeleteAPIView.as_view(), name='account-api-profile-image-delete'),
    url(r'^api/v1/account/logo/delete/$', BusinessLogoDeleteAPIView.as_view(), name='account-api-business-logo-delete'),
    url(r'^api/v1/account/password/change/$', ChangePasswordAPIView.as_view(), name='account-api-change-password'),
    url(r'^api/v1/account/statistics/(?P<pk>\d+)/$', MyStatisticsAPIView.as_view(), name='account-statistics'),
    url(r'^api/v1/plugged/videos/(?P<user_id>\d+)/$', VideoPluggedAPIView.as_view(), name='video-plugged-api'),
    url(r'^api/v1/following/(?P<user_id>\d+)/$', VideoFollowAPIView.as_view(), name='video-plugged-api'),
    url(r'^api/v1/liked/skigit/(?P<pk>\d+)/$', LikedSkigitAPIView.as_view(), name='liked-skigit-api'),
    url(r'^api/v1/favourite/skigit/(?P<pk>\d+)/$', FavouriteSkigitAPIView.as_view(), name='favourite-skigit-api'),
    url(r'^api/v1/helphul-stuff/$', HelpfulStuffAPIView.as_view(), name='helpful-stuff-api'),
    url(r'^api/v1/skigit-data/(?P<pk>\d+)/$', VideoDetailAPIView.as_view(), name='video-detail-api'),
    url(r'^api/v1/friends/$', ProfileFriendDetailAPIView.as_view(), name='profile-friend-detail-api'),
    url(r'^api/v1/friends/invite/$', ProfileFriendsInviteAPIView.as_view(), name='profile-friends-invite-api'),
    url(r'^api/v1/friend/invite/internal/$', FriendInviteInternalAPIView.as_view(), name='profile-friends-internal-invite-api'),
    url(r'^api/v1/friend/invite/email/$', FriendInviteEmailAPIView.as_view(), name='profile-friends-email-invite-api'),
    url(r'^api/v1/friend/accept/$', FriendAcceptAPIView.as_view(), name='friends-accept-api'),
    url(r'^api/v1/friend/remove/$', FriendRemoveAPIView.as_view(), name='friend-remove-api'),
    url(r'^api/v1/videos/$', VideoListAPIView.as_view(), name='video-list-api'),
    url(r'^api/v1/manage-like/video/$', VideoLikeAPIView.as_view(), name='video-like-api'),
    url(r'^api/v1/manage-follow/user/$', UserFollowAPIView.as_view(), name='user-follow-api'),
    url(r'^api/v1/manage-favourite/video/(?P<video_id>\d+)/$', VideoFavouriteAPIView.as_view(), name='video-favourite-api'),
    url(r'^api/v1/statistics/video/(?P<video_id>\d+)/$', VideoStatisticsAPIView.as_view(), name='video-statistics-api'),
    url(r'^api/v1/in-appropriate/reason/$', InappropriateReasonAPIView.as_view(), name='in-appropriate-reason-api'),
    url(r'^api/v1/manage-flag/video/(?P<video_id>\d+)/$', VideoFlagAPIView.as_view(), name='video-flag-api'),
    url(r'^api/v1/manage-share/video/$', VideoShareAPIView.as_view(), name='video-share-api'),
    url(r'^api/v1/manage-copyright/video/(?P<video_id>\d+)/$', CopyrightInfringementAPIView.as_view(), name='video-copyright-api'),
    url(r'^api/v1/donate/groups/$', DonateGroupsAPIView.as_view(), name='donate-groups-api'),
    url(r'^api/v1/video/upload/init/$', VideoUploadInitAPIView.as_view(), name='video-upload-init-api'),
    url(r'^api/v1/video/upload/$', VideoUploadAPIView.as_view(), name='video-upload-api'),
    url(r'^api/v1/video/plugin/(?P<plug_id>\d+)/$', VideoPluginAPIView.as_view(), name='video-plugin-upload-api'),
    url(r'^api/v1/video/delete/$', VideoDeleteAPIView.as_view(), name='video-delete-api'),
    url(r'^api/v1/video/un-plug/$', UnPlugVideoView.as_view(), name='video-un-plug-api'),
    url(r'^api/v1/category/$', CategoryAPIView.as_view(), name='category-api'),
    url(r'^api/v1/subject/category/$', SubjectCategoryAPIView.as_view(), name='category-api'),
    url(r'^api/v1/business-user/$', BusinessUserListAPIView.as_view(), name='business-user-api'),
    url(r'^api/v1/profile/(?P<username>[\w.@+-]+)/$', ProfileDetailAPIView.as_view(), name='profile-detail-api'),
    url(r'^api/v1/get-sperk/(?P<sperk_user_id>\d+)/$', GetSperkAPIView.as_view(), name='get-sperk-api'),
    url(r'^api/v1/sperk/detail/(?P<sperk_user_id>\d+)/$', SperkDetailAPIView.as_view(), name='sperk-detail-api'),
    url(r'^api/v1/search/video/$', VideoSearchAPIView.as_view(), name='search-video-api'),
    url(r'^api/v1/sperk/list/$', SperkListAPIView.as_view(), name='sperk-list-api'),
    url(r'^api/v1/payment/gateway/token/$', PaymentGatewayTokenAPIView.as_view(), name='payment-gateway-token-api'),
    url(r'^api/v1/create/payment/customer/$', CreatePaymentCustomerAPIView.as_view(), name='create-payment-customer-api'),
    url(r'^api/v1/payment/customer/detail/$', PaymentCustomerDetailAPIView.as_view(), name='payment-customer-detail-api'),
    url(r'^api/v1/delete/payment/$', DeletePaymentTypeAPIView.as_view(), name='delete-payment-customer-api'),
    url(r'^api/v1/invoices/$', InvoiceListAPIView.as_view(), name='invoices-list-api'),
    url(r'^api/v1/invoice/pay/$', InvoicePayAPIView.as_view(), name='invoice-payment-api'),
    url(r'^api/v1/general/notifications/$', GeneralNotificationsAPIView.as_view(), name='general-notification-api'),
    url(r'^api/v1/friend/invite/notifications/$', FriendInviteNotificationsAPIView.as_view(), name='friend-invite-notification-api'),
    url(r'^api/v1/notifications/count/$', NotificationCountAPIView.as_view(), name='notification-count-api'),
    url(r'^api/v1/notification/delete/$', DeleteNotificationAPIView.as_view(), name='delete-notification-api'),
    url(r'^api/v1/notification/read/$', ReadNotificationAPIView.as_view(), name='read-notification-api'),
    url(r'^api/v1/share/social-network/$', ShareSocialnetworkAPIView.as_view(), name='share-social-network-api'),
    url(r'^api/v1/social/network/register/$', SocialnetworkRegisterAPIView.as_view(), name='social-network-register-api'),
    url(r'^api/v1/rest-auth/facebook/$', FacebookLoginAPI.as_view(), name='fb_api_login'),
    url(r'^api/v1/rest-auth/twitter/$', TwitterLoginAPI.as_view(), name='twitter_api_login'),
    url(r'^api/v1/rest-auth/instagram/$', InstagramLoginAPI.as_view(), name='instagram_api_login'),
    url(r'^api/v1/rest-auth/linkedin/$', LinkedinLoginAPI.as_view(), name='linkedin_api_login'),
    url(r'^api/v1/url-list/$', UrlListAPIView.as_view(), name='url-list-api'),
    url(r'^api/v1/skigit-view/$', SkigitViewFeeAPIView.as_view(), name='skigit_api_view'),
    url(r'^api/v1/weblink-fee/$', SkigitWebLinkFeeAPIView.as_view(), name='skigit_api_weblink'),
    url(r'^api/v1/logo-fee/$', SkigitBusinessLogoFeeAPIView.as_view(), name='skigit_api_business_logo'),
    url(r'^api/v1/qrcode-fee/$', SkigitQRCodeFeeAPIView.as_view(), name='skigit_api_qr_code'),
    url(r'^api/v1/social-post-fee/$', SkigitSocialPostFeeAPIView.as_view(), name='skigit_api_post_fee'),
    url(r'^api/v1/embed-fee/$', SkigitEmbedFeeAPIView.as_view(), name='skigit_api_embed_fee'),
    url(r'^api/v1/internal-embed-fee/$', SkigitInternalEmbedFeeAPIView.as_view(), name='skigit_api_interal_embed_fee'),
    url(r'^api/v1/learn-more-fee/$', SkigitLearnMoreFeeAPIView.as_view(), name='skigit_api_learn_more_fee'),
    url(r'^api/v1/video/(?P<video_id>\d+)/plugin-map/$', SkigitPluginMapApiView.as_view(), name='skigit_api_plugin_map'),
    url(r'^api/v1/video/(?P<videoId>\d+)/plugins/$', VideoListAPIView.as_view(), name='skigit_api_video_plugins'),
    url(r'^api/v1/update-two-fa/$', UpdateTwoFaAPIView.as_view(), name='skigit_api_update_two_fa'),
    url('^api/v1/send-OTP/$', sendOtpAPIView.as_view(),name='skigit_api_send_otp'),
    url('^api/v1/verify-OTP/$', verifyOtpAPIView.as_view(),name='skigit_api_verify_otp'),
    url('^api/v1/check_phone_validity/$', isPhoneValidAPIView.as_view(),name='skigit_api_phone_validity'),
    url(r'^api/v1/account/logout/', LogoutAPIView.as_view(), name='skigit_api_logout'),
   # url(r'^api/v1/account/login/', LoginAPIViewSet.as_view(), name='skigit_api_login'),

    # Admin data Fetch/upload APIs
    path('api/v1/migrate/admin/', AdminDataMigrateAPIView.as_view()),
    path('api/v1/migrate/admin/update/', AdminDataMigrateUpdateAPIView.as_view()),

    url(r'^referal/$', ShareManageDeeplinkView.as_view(), name='share_deeplink_view')

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT, show_indexes=True)

urlpatterns += [url(r'^static/(?P<path>.*)$', view_static_server, {'document_root': settings.STATIC_ROOT}),
                    url(r'^media/(?P<path>.*)$', view_static_server, {'document_root': settings.MEDIA_ROOT})]

urlpatterns += [path('.well-known/acme-challenge/<str:renew>/', Home.as_view()), path('.well-known/acme-challenge/<str:renew>/:', Home.as_view())]

handler404 = "core.views.redirect_page_not_found"
handler500 = "core.views.redirect_server_error"

# Change this after converting from runserver command to nginx/apache in Production server
if not settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'__debug__', include(debug_toolbar.urls)),
    ]
