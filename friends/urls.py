
from django.conf.urls import url
from friends.views import *

urlpatterns = [
    url(r'^friends-&-invite/$', FriendsInvite.as_view(), name='friends_&_invite'),
    url(r'^friend-search/$', friendsinvitesearch, name='friends_invite_search'),
    url(r'^friend-share-search/$', friendssharesearch, name='friends_share_search'),
    url(r'^friends-internal-invite/$', internalInviteRequest, name='internal_invite'),
    url(r'^friends-request-approve/$', approveFriendRequest, name='accept_as_friend'),
    url(r'^friends-request-rejected/$', rejectFriendRequest, name='reject_invite'),
    url(r'^new-friend-invite/$', newFriendRequest, name='new_invite'),
    url(r'^friend-notification/$', friendNotifications, name='friend_notifications'),
    url(r'^friend-count-notification/$', friendNotificationsCount, name='friend_notifications_count'),
    url(r'^share-skigit-date/$', share_skigit_date, name='share_skigit_date'),
    url(r'^notification-ski/$', notifications_ajax, name='ski_notification'),
    url(r'^notification-delete/$', remove_notify_ajax, name='delete_notification'),
    url(r'^internal-embed-post/$', internal_embed_ajax, name='internal_embed'),
    url(r'^un-embed-skigit/$', remove_embed_ajax, name='un_embed_skigit'),
    url(r'^brochure-skigit-24x36/$', wall_post_skigit24x36, name='wall_post_24x36'),
    url(r'^wall-poster-b-logos/$', get_b_logo, name='wall_poster_b_logos'),
    url(r'^set-poster-b-logo/$', set_b_logo, name='set_poster_b_logos'),
    url(r'^set-brochure-logo/$', set_brochure_logo, name='set_brochure_logo'),
    url(r'^brochure-print/$', brochure_print, name='brochure_print'),
     url(r'^wallpaper-print/$', wallpaper_print, name='wallpaper_print'),
    url(r'^set-brochure/$', set_brochure, name='set_brochure'),
    url(r'^set_wall_poster/$', set_wall_poster, name='set_wall_poster'),
     
]
