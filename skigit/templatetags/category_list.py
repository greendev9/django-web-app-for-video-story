import random
from django import template
from django.core.cache import cache
from django.contrib.auth.models import User
from user.models import Profile, BusinessLogo
from skigit.models import Category, Like
from social.models import Follow
from django.template import RequestContext
from django.db.models import Q
from friends.models import Friend, Notification
from django.conf import settings
from core.utils import get_all_logged_in_users, deleteDisabled
from friends.views import notification_settings
from el_pagination.templatetags.el_pagination_tags import paginate
from el_pagination.paginators import LazyPaginator

register = template.Library()


@register.inclusion_tag('template/category_link.html')
def category_link():
    category = Category.objects.filter(is_active=True)
    return {
        'category_list': category,
    }


@register.inclusion_tag('navbar.html', takes_context=True)
def user_navigation(context):
    return_context = RequestContext(context['request'])
    request = context['request']
    user, category = None, None
    category = Category.objects.filter(is_active=True)
    user_profile, message_notification, friend_request_notification, var1, var2, genral_notification, like_notification, follow_notification = None, None, None, None, None, None, None, None
    friend_list = []
    if request.user.is_authenticated:
        user = request.user
        user = User.objects.get(pk=request.user.id)
        user_profile = Profile.objects.get(user=user)

        like_notification = Like.objects.filter(skigit__user=user, status=True, is_read=False).count()
        follow_notification = Follow.objects.filter(follow=user, status=True, is_read=False).count()

        general_notify_count = Notification.objects.filter(user=user, is_view=False, is_read=False, is_active=True).count()
        if general_notify_count == 0:
            general_notify_count = None

        if notification_settings(user.id, 'friends_request_notify') and Friend.objects.filter((Q(from_user=user) | Q(to_user=user)), is_read=False).exists():
            var1 = Friend.objects.filter(to_user=user, status=0, is_read=False).count()
            friend_request_notification = var1

        if user_profile.profile_img:
            return_context['profile_image'] = 'http://' + request.get_host() + user_profile.profile_img.url
        return_context['request'] = request
        return_context['user'] = user
        return_context['user_profile'] = user_profile
        return_context['category_list'] = category
        return_context['backend_name'] = cache.get('backend')
        return_context['users'] = get_all_logged_in_users()
        return_context['general_notify_count'] = general_notify_count

        if message_notification is not None and len(message_notification) > 0:
            return_context['message_notification'] = len(message_notification)

        if friend_request_notification is not None:
            return_context['friend_request_notification'] = friend_request_notification
            return_context['friend_list'] = friend_list

        if like_notification and like_notification is not None and follow_notification and follow_notification is not None:
            return_context['genral_notification'] = (int(like_notification) + int(follow_notification))
        elif like_notification and like_notification is not None:
            return_context['genral_notification'] = int(like_notification)
        elif follow_notification and follow_notification is not None:
            return_context['genral_notification'] = int(follow_notification)
        else:
            return_context['genral_notification'] = None
    else:
        return_context.update({'request': request, 'user': user, 'user_profile': user_profile,
                               'category_list': category, 'backend_name': cache.get('backend'),
                               'users': get_all_logged_in_users()})
    return return_context


@register.inclusion_tag('template/user_navigation.html', takes_context=True)
def friends_request(context):
    return_context = RequestContext(context['request'])
    request = context['request']

    if request.user.is_authenticated:
        user = User.objects.get(pk=request.user.id)
        if Friend.objects.filter((Q(from_user=user) | Q(to_user=user)), is_read=False).exists():
            friends_count = Friend.objects.filter((Q(from_user=user) |
                                                   Q(to_user=user)),
                                                  is_read=False).count()
            if friends_count:
                return_context['friend_notification'] = friends_count
    return return_context


@register.filter(name='addcss')
def addcss(field, css):
    try:
        return field.as_widget(attrs={"class": css})
    except Exception:
        pass


@register.filter(name='is_bus')
def is_bus(user):
    try:
        is_bus = user.groups.filter(name=settings.BUSINESS_USER).exists()
        if is_bus and is_bus is not None:
            return True
        else:
            return False
    except:
        return False  # group doesn't exist, so for sure the user isn't part of the group

@register.filter
def can_pay_now(month_num, year):
    import calendar
    from datetime import datetime
    # invoice month and last day
    month, last_day = calendar.monthrange(int(year), int(month_num))

    # current month and last day
    today = datetime.today()
    if today.year > int(year) or (today.year == int(year) and today.month > int(month_num)):
        return True
    else:
        return False

@register.filter
def delete_disabled(vid):
    return deleteDisabled(vid)

@register.filter
def date_plus_days(date, days):
    from datetime import timedelta
    return date + timedelta(days=days)

class VideoListLazyPaginator(LazyPaginator):

    def page(self, number):
        page_obj = super(VideoListLazyPaginator, self).page(number)
        # page function returns page object from that you could access object_list
        videos_latest = page_obj.object_list
        # random.shuffle(videos_latest)      # reshuffle video list to make it random

        # Do some processing here for your queryset
        vid_profiles = []
        for vid_profile in videos_latest:
            if vid_profile.made_by and vid_profile.made_by.id not in vid_profiles:
                vid_profiles.append(vid_profile.made_by.id)

        profiles = Profile.objects.filter(user_id__in=vid_profiles)
        profile_ids = [p.id for p in profiles]
        logos = BusinessLogo.objects.filter(profile__id__in=profile_ids, is_deleted=False).distinct('id').values(
            'profile__id', 'id', 'logo')

        for i in range(len(videos_latest)):
            for p in profiles:
                if videos_latest[i].made_by and videos_latest[i].made_by.id == p.user_id:
                    for l in logos:
                        if l['profile__id'] == p.id:
                            videos_latest[i].default_logo = l
                            break
                    break

        page_obj.object_list = videos_latest
        return page_obj

@register.tag
def video_lazy_paginate(parser, token):
    return paginate(parser, token, paginator_class=VideoListLazyPaginator)
