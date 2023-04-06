# -*- coding: utf-8 -*-

import urllib
import json
from django.shortcuts import render
from django.template.context import RequestContext
from django.contrib.auth.models import Group
from skigit.models import Profile
import logging
from skigit_project import settings
from core.signals import send_user_created_email
from django.core.cache import cache
from django.shortcuts import render

logger = logging.getLogger(__name__)


def save_profile(backend, user, response, *args, **kwargs):
    """

    Args:
        backend:
        user:
        response:
        *args:
        **kwargs:
    """
    cache.set('backend', backend.name)
    username = user.get_full_name()
    if username is None or username is '' or username == '':
        username = user.get_username()
    else:
        username = None
    if backend.name == 'facebook' and not Profile.objects.filter(user=user).exists():
            Profile.objects.create(user=user)
            if cache.get('account_type') == 'general':
                group = Group.objects.get(name=settings.GENERAL_USER)
            elif cache.get('account_type') == 'business':
                group = Group.objects.get(name=settings.BUSINESS_USER)
            else:
                group = Group.objects.get(name=settings.GENERAL_USER)
            user.groups.add(group)
            user.save()
            send_user_created_email(username, user.email)
    if backend.name == 'twitter' and not Profile.objects.filter(user=user).exists():
            Profile.objects.create(user=user)
            if cache.get('account_type') == 'general':
                group = Group.objects.get(name=settings.GENERAL_USER)
            elif cache.get('account_type') == 'business':
                group = Group.objects.get(name=settings.BUSINESS_USER)
            else:
                group = Group.objects.get(name=settings.GENERAL_USER)
            user.groups.add(group)
            user.save()
            send_user_created_email(username, user.email)
    if backend.name == 'yahoo' and not Profile.objects.filter(user=user).exists():
            Profile.objects.create(user=user)
            if cache.get('account_type') == 'general':
                group = Group.objects.get(name=settings.GENERAL_USER)
            elif cache.get('account_type') == 'business':
                group = Group.objects.get(name=settings.BUSINESS_USER)
            else:
                group = Group.objects.get(name=settings.GENERAL_USER)
            user.groups.add(group)
            user.save()
            # send_user_created_email(username, user.email)
    if backend.name == 'linkedin-oauth2' and not Profile.objects.filter(user=user).exists():
            Profile.objects.create(user=user)
            if cache.get('account_type') == 'general':
                group = Group.objects.get(name=settings.GENERAL_USER)
            elif cache.get('account_type') == 'business':
                group = Group.objects.get(name=settings.BUSINESS_USER)
            else:
                group = Group.objects.get(name=settings.GENERAL_USER)
            user.groups.add(group)
            user.save()
            send_user_created_email(username, user.email)
    if backend.name == 'google-oauth2' and not Profile.objects.filter(user=user).exists():
            Profile.objects.create(user=user)
            if cache.get('account_type') == 'general':
                group = Group.objects.get(name=settings.GENERAL_USER)
            elif cache.get('account_type') == 'business':
                group = Group.objects.get(name=settings.BUSINESS_USER)
            else:
                group = Group.objects.get(name=settings.GENERAL_USER)
            user.groups.add(group)
            user.save()
            send_user_created_email(username, user.email)


def update_user_social_data(backend, strategy, *args, **kwargs):
    """

    Args:
        backend:
        strategy:
        *args:
        **kwargs:

    Returns:

    """
    cache.set('backend', backend.name)
    if backend.name == 'facebook':
        if not kwargs['is_new']:
            return

        user = kwargs['user']

        f_bu_id = kwargs['response']['id']
        access_token = kwargs['response']['access_token']

        url = u'https://graph.facebook.com/{0}/' \
              u'?fields=email' \
              u'&access_token={1}'.format(f_bu_id, access_token,)
        request = urllib.request.Request(url)
        email = json.loads(urllib.request.urlopen(request).read()).get('email')
        user.email = email
        user.save()


def social_login_type(request, social_type):
    """

    Args:
        request:
        social_type:

    Returns:

    """
    if request.method == 'GET':
        account_type = request.POST.get('acc_type')
        social_name = social_type
        return render(request, 'social_registration/social_registration_type.html', locals())
    if request.method == 'POST':
        social_name = social_type
        account_type = request.POST.get('acc_type')
        if account_type == 'general':
            cache.set("account_type", None)
            cache.set('account_type', account_type)

        elif account_type == 'business':
            cache.set("account_type", None)
            cache.set('account_type', account_type)
        return render(request, 'social_registration/social_registration_type.html', locals())


def social_auth_login(request):
    """

    Args:
        request:

    Returns:

    """
    context = RequestContext(request, {'request': request, 'user': request.user})
    return render('index.html', context_instance=context)
