import logging

from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.shortcuts import render
from friends.models import *
from invoices.views import business_internal_embed_fees
from skigit.models import Profile, VideoDetail
from social.models import Follow, Share
from core.utils import (json_response, require_filled_profile, payment_required, get_object_or_None, is_user_business,
						CustomIsAuthenticated, get_all_logged_in_users)
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from heapq import merge
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

from rest_framework import generics, views
from rest_framework.response import Response

from skigit_project import settings
from datetime import datetime, timedelta
import pytz
import json

from user.serializers import ProfileFriendsInviteSerializer, api_request_images
from .serializers import FriendNotificationsAPISerializer, GeneralNotificationsAPISerializer
from core.views import SkigitBaseView
import base64
from django.core.files.base import ContentFile

logger = logging.getLogger('Friends')

from meta.views import Meta

# Generic functions

def delete_notification(data):
	response_data = {'is_success': False, 'message': 'Notification Failed to remove'}

	try:
		to_user = data.get('to_user', '')
		t_user = get_object_or_None(User, id=int(to_user))

		if t_user:
			msg_type = data.get('msg_type', '')
			from_user = data.get('from_user', '')
			skigit_id = data.get('skigit_id', '')
			f_user = get_object_or_None(User, id=int(from_user))

			if msg_type in data:
				if Notification.objects.filter(user=t_user, skigit_id=int(skigit_id),
											   from_user=f_user, msg_type=msg_type).exists():
					Notification.objects.filter(user=t_user, skigit_id=int(skigit_id),
												from_user=f_user, msg_type=msg_type).update(msg_type='deleted_msg')
					Notification.objects.filter(msg_type='deleted_msg').delete()
					response_data['is_success'] = True
					response_data['message'] = 'Notification Removed.'
				else:
					response_data['is_success'] = True
					response_data['message'] = 'Notification is already removed.'
			else:
				if Notification.objects.filter(user=t_user, from_user=f_user, msg_type=msg_type).exists():
					Notification.objects.filter(user=t_user, from_user=f_user,
												msg_type=msg_type).update(msg_type='deleted_msg')
					Notification.objects.filter(msg_type='deleted_msg').delete()
					response_data['is_success'] = True
					response_data['message'] = 'Notification Removed.'
				else:
					response_data['is_success'] = True
					response_data['message'] = 'Notification is already removed.'
		else:
			response_data['is_success'] = False
			response_data['message'] = 'Please login and try again.'
	except Exception as exc:
		logger.error("Delete notification is failed: ", exc)
		response_data['is_success'] = False
		response_data['message'] = 'Notification Failed to remove.'
	return response_data

def read_notification(data):
	response_data = {'is_success': False, 'message': 'Notification Failed to read'}

	try:
		user_id = data.get('user_id', '')
		user = get_object_or_None(User, id=user_id)

		if user:
			notification = Notification.objects.filter(id=data.get('notification_id', ''),
													   user__id=user_id)
			if notification.exists():
				notification.update(is_read=True)
				response_data['is_success'] = True
				response_data['message'] = 'Notification is read'
			else:
				response_data['is_success'] = False
				response_data['message'] = 'Please login and try again.'
		else:
			response_data['is_success'] = False
			response_data['message'] = 'Please login and try again.'
	except Exception as exc:
		logger.error("Read notification is failed: ", exc)
		response_data['is_success'] = False
		response_data['message'] = 'Notification Failed to read.'
	return response_data

def get_general_notifications_count(user_id):
	response_data = {'is_success': False, 'message': 'Error in get user notification'}
	try:
		user = get_object_or_None(User, id=user_id)
		count = Notification.objects.filter(user=user, is_view=False, is_read=False, is_active=True).count()
		response_data['is_success'] = True
		response_data['message'] = 'Success in ajax call'
		response_data['count'] = count
	except Exception as exc:
		logger.error("General Notification count throws error: ", exc)
	return response_data

def get_friend_notifications_count(user_id):
	response_data = {'result': False, 'messages': ' Error into Notification count', 'count': 0}

	try:
		user = get_object_or_None(User, id=user_id, is_active=True)
		if notification_settings(user_id, 'friends_request_notify') and Friend.objects.filter((Q(from_user=user) | Q(to_user=user)), is_read=False).exists():
			friend_count = Friend.objects.filter(to_user=user, status=0, is_read=False).count()
			response_data['count'] = friend_count
			response_data['result'] = True
			response_data['messages'] = '%s Friend Invitation pending' % friend_count
		else:
			response_data['count'] = 0
			response_data['result'] = False
			response_data['messages'] = '0 Friend Invitation pending'
	except Exception as exc:
		logger.error("Friend Notification count throws error: ", exc)
	return response_data

def get_general_notifications(data):
	response_data = {'is_success': False,
					 'message': 'No notifications to display!'}

	time_zone = data.get('time_zone', '')
	user_id = data.get('user_id', '')
	user = get_object_or_None(User, id=user_id)
	notification_list = []
	plug_message = []
	parent_title = skigit_detail_id = child_skigi_id = parent_skigi_id = child_title = None
	header_text = {'like': 'Congratulations!', 'plug': 'Congratulations!', 'plug-plug': 'Coincidence? I think not!',
				   'friends': 'Wanna new friend?', 'friends_accepted': "Sure, let’s be friends!",
				   'un_plug': "We’re sorry.. your got  unplugged.", 'new_post': 'Congratulations!',
				   'new_post_follow': 'Following Post!', 'follow': 'Congratulations!', 'unapproved': "We're sorry...",
				   'share': 'You are on the Radar!', 'plug_primary': 'The Primary skigit', 'unfollow': "We’re sorry..",
				   'video_uploaded': 'Video uploaded!', 'video_not_uploaded': 'Video not uploaded!'}

	if Notification.objects.filter(user=user, is_read=False).exists():
		Notification.objects.filter(msg_type__icontains='_deleted').delete()
		start_date = datetime.now() - timedelta(days=30)
		end_date = datetime.now()
		Notification.objects.filter(user=user, is_read=False).update(is_view=True)
		notify_obj = Notification.objects.filter(user=user, created_date__range=(start_date, end_date),
												is_read=False, is_active=True).order_by('-created_date')
		for notify in notify_obj:
			if notify.skigit_id and Video.objects.filter(id=int(notify.skigit_id)).exists():
				video = Video.objects.get(id=int(notify.skigit_id))
				vid_title = video.title
				if VideoDetail.objects.filter(skigit_id__id=int(notify.skigit_id)).exists():
					video_detail = VideoDetail.objects.get(skigit_id__id=int(notify.skigit_id))
					skigit_detail_id = video_detail.id
			else:
				vid_title = None
			if notify.msg_type == 'plug_primary':
				if not (str(notify.message).find("*@p*")) == -1:
					plug_message = int((notify.message).split("*@p*")[-1])
					plug_detail = Video.objects.filter(id=int(plug_message)).values_list('title', flat=True)
					parent_title = plug_detail[0]
					video_de = VideoDetail.objects.get(title=plug_detail[0])
					parent_skigi_id = video_de.id
				elif not (str(notify.message).find("*@c*")) == -1:
					plug_message = int((notify.message).split("*@c*")[-1])
					plug_detail = Video.objects.filter(id=int(plug_message)).values_list('title', flat=True)
					child_title = plug_detail[0]
					video_de = VideoDetail.objects.get(title=plug_detail[0])
					child_skigi_id = video_de.id
				else:
					plug_message = None

			message_type = notify.msg_type
			if is_user_business(notify.from_user):
				user_type = 'business'
				view_general = 'yes' if message_type in ["friends", "friends_accepted"] else 'no'
			else:
				user_type = 'general'
				view_general = 'yes'

			notification_tmp = {'id': notify.id,
								'message_type': message_type,
								'message': notify.message,
								'user': notify.user.id,
								'username': notify.user.username,
								'skigit_id': notify.skigit_id,
								'from_user_name': notify.from_user.username,
								'from_user_id': notify.from_user.id,
								'is_read': notify.is_read,
								'view_general': view_general,
								'from_user_type': user_type,
								'created_date': notify.created_date,
								'header': header_text[message_type] if message_type in header_text else ''}

			if message_type in ["plug", "plug-plug", "un_plug", "new_post",
								"new_post_follow", "unapproved", "share", "plug_primary",
								"like","video_uploaded"]:
				notification_tmp.update({'video_title': vid_title,
										 'video_id': skigit_detail_id})

			if notify.msg_type == "plug_primary":
				if parent_title:
					notification_tmp.update({'plug_video_title': parent_title,
											 'plug_video_id': parent_skigi_id})
				if child_title:
					notification_tmp.update({'plug_video_title': child_title,
											 'plug_video_id': child_skigi_id})

			notification_list.append(notification_tmp)

		response_data['is_success'] = True
		response_data['message'] = 'Successfully get the notification list'
		response_data['notify_list'] = notification_list
	else:
		response_data['is_success'] = False
		response_data['message'] = 'No notifications to display!'
		response_data['notify_list'] = notification_list
	return response_data

def get_friend_invite_notifications(user_id, data, api_request=False):
	friend_list = []
	response_data = {'result': False, 'messages': 'Error in the Notifications.'}
	user = get_object_or_None(User, id=user_id, is_active=True)
	user_profile = user.profile

	try:
		if notification_settings(user_id, 'friends_request_notify') and Friend.objects.filter((Q(from_user__id=user_id) | Q(to_user__id=user_id)), is_read=False).exists():
			friends = Friend.objects.prefetch_related('from_user').filter(to_user__id=user_id, status=0, is_read=False)
			for friend in friends:
				friend_from_user_id = friend.from_user.id
				us = friend.from_user
				ps = us.profile
				name = us.get_full_name()
				l_img = api_request_images(ps.profile_img, quality=99, format='PNG') if ps.profile_img else None
				friend_list.append(
					{'to_user': friend_from_user_id, 'name': name, 'profile_img': l_img, 'status': friend.status,
					 'username': us.username})
			friend_list = sorted(friend_list, key=lambda k: k['name'])
			response_data['friend_list'] = friend_list
			response_data['result'] = True
			response_data['messages'] = 'Received notification list'
		else:
			response_data['friend_list'] = friend_list
			response_data['result'] = False
			response_data['messages'] = 'There is no pending Notifications.'
	except Exception as exc:
		response_data['friend_list'] = friend_list
	return response_data


def remove_friend(cur_user_id, to_user_id):
	response_data = {'result': False,
					 'message': ''}
	notifications = []
	cur_user = get_object_or_None(User, id=cur_user_id, is_active=True)
	user_obj = get_object_or_None(User, id=to_user_id, is_active=True)
	if Friend.objects.filter(from_user=user_obj, to_user=cur_user).exists():
		Friend.objects.filter(from_user=user_obj, to_user=cur_user).delete()
		notifications = Notification.objects.filter(from_user=user_obj, user=cur_user)
		response_data['result'] = True
	elif Friend.objects.filter(from_user=cur_user, to_user=user_obj).exists():
		notifications = Notification.objects.filter(from_user=cur_user, user=user_obj)
		Friend.objects.filter(from_user=cur_user, to_user=user_obj).delete()
		response_data['result'] = True

	if notifications:
		response_data['result'] = True
		notifications.filter(msg_type='friends').update(msg_type='un_friend')
		notifications.filter(msg_type='friends_accepted').update(msg_type='un_friend')
		notifications.filter(msg_type='un_friend').delete()
	return response_data

def get_friends_invite_search_result(user_id, search, api_request=False, page=1):

	search_list = []
	users_per_page = 10
	response_data = {'result': False,
					 'is_success': True,
					 'search_list': search_list}
	term = search.split()
	if len(term) > 2:
		response_data.update(is_success=False, message="Record not found.")
		return response_data
	try:
		kwargs = {
			'first_name__istartswith': term[0],
			'is_active' : True
		}
		if len(term) > 1:
			kwargs['last_name__istartswith'] = term[1]

		query_result = User.objects.exclude(id=user_id).filter(**kwargs).order_by('first_name')
		if api_request:
			page_obj = query_result
		else:
			page_result = Paginator(query_result, users_per_page)
			page_obj = page_result.get_page(page)
			
		for qs in page_obj:
			try:
				ps = qs.profile
				if ps.is_completed['status']:
					friend = Friend.objects.filter(from_user__id=user_id, to_user=qs.id)
					if friend.exists():
						status = friend.last().status
						if status == '1':
							title = "Friends"
						elif status == '3':
							title = "Invite"
						else:
							title = "Invitation Sent"
					elif Friend.objects.filter(from_user__id=qs.id, to_user__id=user_id).exists():
						status = Friend.objects.filter(from_user__id=qs.id, to_user__id=user_id).last().status
						if status == '1':
							title = "Friends"
						elif status == '3':
							title = "Invite"
						else:
							title = "Accept"
					else:
						status = '3'
						title = 'Invite'
					if ps.profile_img:
						qs.l_img = api_request_images(ps.profile_img, quality=99, format='PNG')
					else:
						qs.l_img = "{0}{1}".format(settings.STATIC_URL,
												   'skigit/detube/images/noimage_user.jpg')
					search_list.append({'uid': qs.id, 'username': qs.username, 'name': qs.get_full_name(), 'image': qs.l_img,
										'status': status, 'title': title})
			except Exception as exc:
				continue
	except Exception as exc:
		response_data.update(is_success=False,
							 message="The friends are not loaded. Please try again.")
	if not api_request:
		response_data.update(next_page=page_obj.next_page_number() if page_obj.has_next() else 0)
	return response_data


def check_friend_of_friends(cur_user, user_obj):
	
	friends = Friend.objects.filter(to_user=user_obj).filter(status=1)#.all()
	
	for friend in friends:
		if Friend.objects.filter(to_user=friend.from_user).filter(from_user=cur_user).filter(status=1).exists():
			return True

	return False

def invite_friend_internal(cur_user_id, to_user_id):
	response_data = {'result': True,
					 'message': 'Your invitation was sent!'}

	try:
		cur_user = get_object_or_None(User, id=cur_user_id, is_active=True)
		f_nt_message = ""
		f_nt_message += "Wanna new friend? "
		f_nt_message += cur_user.username
		f_nt_message += " wants to be friends With you."
		user_obj = get_object_or_None(User, id=to_user_id, is_active=True)
		
		#check the current user is a friend of inviting user.
		if user_obj and not user_obj.profile.everyone_allowance and not check_friend_of_friends(cur_user, user_obj):
			response_data.update(result=False, message='You can not send invitation to this user.')
			return response_data

		if user_obj and user_obj.profile.is_completed['status']:
			if not Friend.objects.filter(from_user__id=cur_user_id, to_user=user_obj).exists():
				friend = Friend()
				friend.from_user = cur_user
				friend.to_user = user_obj
				friend.status = '0'
				friend.save()

				if notification_settings(user_obj.id, 'friends_request_notify') == True:
					if not Notification.objects.filter(msg_type='friends', user__id=to_user_id,
													   from_user__id=cur_user_id).exists():
						Notification.objects.create(user=user_obj, from_user=cur_user, msg_type='friends',
													message=f_nt_message)
			elif Friend.objects.filter(from_user__id=cur_user_id, to_user__id=to_user_id).exists():
				Friend.objects.filter(from_user__id=cur_user_id, to_user__id=to_user_id).update(status='0')
				if notification_settings(to_user_id, 'friends_request_notify') == True:
					if not Notification.objects.filter(msg_type='friends', user__id=to_user_id,
													   from_user__id=cur_user_id).exists():
						Notification.objects.create(user=user_obj, from_user=request.user, msg_type='friends',
													message=f_nt_message)
													
			response_data['user'] = user_obj.get_full_name()

	except Exception as exc:
		logger.error("Invite friend internal is failure!", exc)
		response_data.update(result=False,
							 message="The friend request was not sent successfully")
							 
	return response_data

def invite_email_friend(cur_user_id, emails):
	'''

	:param cur_user_id: Currrent request logged in user id
	:param email: Email to be sent the invitation
	:return: message
	'''

	response_data = {'result': True,
					 'messages': ''}

	try:
		cur_user = get_object_or_None(User, id=cur_user_id, is_active=True)
		for email in json.loads(emails):
			new_friend = email

			if not User.objects.filter(email=new_friend).exists():
				invitation = FriendInvitation.objects.filter(from_user__id=cur_user.id, to_user_email=new_friend)
				response_data['messages'] = "Your invitations were sent!"
				if not invitation.exists():
					invite = FriendInvitation()
					invite.to_user_email = new_friend
					invite.from_user = cur_user
					invite.save()
				else:
					invitation = invitation.last()
					invitation.updated_date = datetime.now()
					invitation.save(update_fields=['updated_date'])
			else:
				response_data['result'] = False
				response_data['messages'] = 'You cannot invite a user that is already registered with Skigit.'
	except Exception as exc:
		logger.error("Invite friend internal is failure!", exc)
		response_data.update(result=False,
								messages='Invitation sent Fail. Please try again later.')

	return response_data

def accept_friend(cur_user_id, to_user, api_request=False):
	response_data = {'result': False}

	try:
		user = get_object_or_None(User, id=cur_user_id)
		user_obj = get_object_or_None(User, id=to_user, is_active=True)
		f_nt_message = " "
		f_nt_message += "Sure, let's be friends! "
		f_nt_message += user.username
		f_nt_message += " has accepted your friendship."

		if Friend.objects.filter(from_user=user_obj, to_user=user, status=0).exists():
			Friend.objects.filter(from_user=user_obj, to_user=user).update(status='1')
			ps = Profile.objects.get(user=user_obj)
			name = user_obj.get_full_name()
			if ps.profile_img:
				l_img = api_request_images(ps.profile_img, quality=99, format='PNG')
				#get_thumbnail(ps.profile_img, '100x100', quality=99, format='PNG').url
			else:
				l_img = "{0}{1}".format(settings.HOST, '/static/skigit/detube/images/noimage_user.jpg')
			follow_count = Follow.objects.exclude(follow=user.id).filter(follow=user_obj).count()
			response_data['result'] = True
			response_data['name'] = name
			response_data['image'] = l_img
			response_data['username'] = user_obj.username
			response_data['count'] = follow_count
			response_data['user_id'] = user_obj.id
			if notification_settings(user_obj.id, 'friends_accept_notify') == True:
				if not Notification.objects.filter(msg_type='friends_accepted', user=user_obj,
												   from_user=user).exists():
					Notification.objects.create(user=user_obj, from_user=user, msg_type='friends_accepted',
												message=f_nt_message)
	except Exception as exc:
		logger.error("Accept friend throws error: ", exc)
		response_data['result'] = False
		response_data['message'] = 'Accept friend request throws error. Please try again.'
	return response_data

def web_push_notifications(m_type, to_user, frm_user, ski_id=None, f_nt_message=None):
	"""
	Function definition for Notification
	:param m_type: Notification Type <Basis of this differentiate the Notification>
	:param to_user: Notification Receiver User
	:param frm_user: Notification Sent after activity by User
	:param ski_id: Video (Skigit ID) Reference
	:param f_nt_message: Notification Messages by Notification type
	"""

	if not Notification.objects.filter(msg_type=m_type, user=to_user, skigit_id=ski_id,
									   from_user=frm_user).exists():
		Notification.objects.create(msg_type=m_type, user=to_user, skigit_id=ski_id, from_user=frm_user,
									message=f_nt_message)
	else:
		new_type = '%s_deleted' % m_type
		Notification.objects.filter(msg_type=m_type, user=to_user,
									from_user=frm_user, skigit_id=ski_id).update(msg_type=new_type, is_view=True,
																				 is_read=True, is_active=False)
		Notification.objects.filter(msg_type=new_type, from_user=frm_user, skigit_id=ski_id,
									user=to_user).delete()
		Notification.objects.create(msg_type=m_type, user=to_user, from_user=frm_user, skigit_id=ski_id,
									message=f_nt_message)


def notification_settings(user, notification_type):
	"""
		Notification Settings
	"""
	try:
		notify = Profile.objects.filter(user__id=int(user)).values(notification_type)
		return notify[0][notification_type]
	except Exception as e:
		message = e.message
		return None


def get_localize_date(utc_dt, time_zone):
	"""
	Function definition for Localizing the Time <UTC to Local Time Conversion function>
	:param utc_dt: Date in UTC (Universal Time Conversion format)(UTC+0:00)
	:param time_zone: Localization Time in Name eg: (Asia/Calcutta) (UTC+5:30)
	:return: Returns localization Date
	"""
	local_tz = pytz.timezone(time_zone)
	local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
	return local_tz.normalize(local_dt)


def get_time_delta(before_date, time_zone):
	"""
	Function Definition for Time Difference between two DateTime (Date)
	:param before_date: Date Which we Can subtract
	:param time_zone: Localization Time in Name eg: (Asia/Calcutta) (UTC+5:30)
	:return: Returns Difference between two date and Time. <In hours/Minute/Seconds/Date with time>
	"""
	end_date = get_localize_date(before_date, time_zone)
	after_date = get_localize_date(datetime.utcnow(), time_zone)
	yesterday = get_localize_date((datetime.utcnow() - timedelta(days=1)), time_zone)
	current_day = after_date.day
	prev_day = yesterday.day
	custom_day = before_date.day
	current_week = after_date.isocalendar()[1]
	custom_week = before_date.isocalendar()[1]
	date_diff = after_date - end_date
	day = date_diff.days
	sec = date_diff.seconds
	minute = date_diff.seconds / 60
	hours = minute / 60

	if day == 0 and sec <= 60 and custom_day == current_day:
		return 'Just now'
	elif day == 0 and sec >= 60 and minute <= 59 and custom_day == current_day:
		return '%s minute ago' % int(minute)
	elif day == 0 and minute >= 60 and hours < 24 and custom_day == current_day:
		return '%s hours ago' % int(hours)
	elif day == 1 or custom_day == prev_day and not day == 0:
		return 'Yesterday at %s' % end_date.strftime('%I:%M %p')
	elif 6 >= day >= 2 and current_week == custom_week:
		return '%s at %s' % (end_date.strftime("%a"), end_date.strftime('%I:%M %p'))
	else:
		return '%s %s at %s' % (end_date.strftime("%b"), end_date.strftime("%d"),
								end_date.strftime('%I:%M %p'))


@method_decorator(login_required(login_url='/login'), name="dispatch")
@method_decorator(payment_required, name="dispatch")
@method_decorator(require_filled_profile, name="dispatch")
class FriendsInvite(SkigitBaseView):
	template = 'friends/friends_invite.html'

	def get(self, request, *args, **kwargs):
		context = self.get_context_data(**kwargs)
		page_template = 'friends/friends_invite_body.html'
		friend_list = []
		follow_list = []
		if User.objects.filter(id=request.user.id, is_active=True).exists():
			if Friend.objects.filter(from_user=request.user.id, status='1', to_user__is_active=True).exists():
				friends = Friend.objects.filter(from_user=request.user.id, status='1', to_user__is_active=True).order_by(
					'-from_user__first_name')
				for friend in friends:
					user_profile = User.objects.get(id=friend.to_user.id)
					ps = Profile.objects.get(user=user_profile)
					name = user_profile.get_full_name()
					follow_count = Follow.objects.exclude(follow=request.user.id).filter(follow=user_profile.id,
																						 status=True).count()
					if ps.profile_img:
						#l_img = get_thumbnail(ps.profile_img, '200x200', quality=99, format='PNG').url
						l_img = api_request_images(ps.profile_img, quality=99, format='PNG')
					else:
						l_img = "{0}{1}".format(settings.STATIC_URL,'images/noimage_user.jpg')
					friend_list.append({'user': user_profile.id, 'name': name, 'profile_img': l_img,
										'status': friend.status, 'username': user_profile.username,
										'count': follow_count})
			if Friend.objects.filter(to_user=request.user.id, status='1', from_user__is_active=True).exists():
				friends = Friend.objects.filter(to_user=request.user.id, status='1', from_user__is_active=True).order_by('-from_user__first_name')
				for friend in friends:
					user_profile = User.objects.get(id=friend.from_user.id)
					ps = Profile.objects.get(user=user_profile)
					name = user_profile.get_full_name()
					follow_count = Follow.objects.exclude(follow=request.user.id).filter(follow=user_profile.id,
																						 status=True).count()
					if ps.profile_img:
						#l_img = get_thumbnail(ps.profile_img, '100x100', quality=99, format='PNG').url
						l_img = api_request_images(ps.profile_img, quality=99, format='PNG')
					else:
						l_img = "{0}{1}".format(settings.STATIC_URL,'images/noimage_user.jpg')
					friend_list.append({'user': user_profile.id, 'name': name, 'profile_img': l_img,
										'status': friend.status, 'username': user_profile.username,
										'count': follow_count})
			friend_list = sorted(friend_list, key=lambda k: k['name'])
			follow_list = Follow.objects.exclude(follow=request.user.id).values_list('follow',
																					 flat=True).filter(
				user=request.user.id,
				status=True)
			context.update({
				'friend_list': friend_list,
				'follow_list': follow_list,
				'facebook_app_id': settings.FACEBOOK_APP_ID,
				'view_general_profile': True
			})

			if request.is_ajax():
				self.template = page_template
			return render(request, self.template, context)


@login_required(login_url='/login')
def friendsinvitesearch(request):
	"""
		Internal Skigit Friends Invitations Search by using First and Last name.
	"""
	if request.method == 'POST' and request.is_ajax():
		search = request.POST.get('search_text', None)
		page = request.GET.get('page', 1)
		try:
			response_data = get_friends_invite_search_result(request.user.id, search, page=page)
			response_data.update(result=True)
		except Exception as exc:
			logger.error("Friends search throws error: ", exc)
			response_data = {'result': False, 'search_list': []}
	return json_response(response_data)


@login_required(login_url='/login')
def internalInviteRequest(request):
	"""
		Internal Friends Invite Request registrations
	"""
	response_data = {'result': False}
	if request.method == 'POST' and request.is_ajax():
		cur_user_id = request.user.id
		to_user_id = request.POST.get('to_user', '')
		response_data = invite_friend_internal(cur_user_id, to_user_id)
	return json_response(response_data)


@login_required(login_url='/login')
def approveFriendRequest(request):
	"""

	:param request:
	:return:
	"""
	response_data = {'result': False}

	if request.method == 'POST' and request.is_ajax():
		to_user = request.POST.get('to_user', None)
		cur_user_id = request.user.id
		response_data = accept_friend(cur_user_id, to_user, api_request=False)
		"""
		user_obj = User.objects.get(id=request.POST.get('to_user', None), is_active=True)
		f_nt_message = " "
		f_nt_message += "Sure, let's be friends! "
		f_nt_message += request.user.username
		f_nt_message += " has accepted your friendship."

		if Friend.objects.filter(from_user=user_obj, to_user=request.user, status=0).exists():
			Friend.objects.filter(from_user=user_obj, to_user=request.user).update(status='1')
			ps = Profile.objects.get(user=user_obj)
			name = user_obj.get_full_name()
			if ps.profile_img:
				l_img = get_thumbnail(ps.profile_img, '100x100', quality=99, format='PNG').url
			else:
				l_img = "{0}{1}".format(settings.STATIC_URL,'skigit/detube/images/noimage_user.jpg')
			follow_count = Follow.objects.exclude(follow=request.user.id).filter(follow=user_obj).count()
			response_data['result'] = True
			response_data['name'] = name
			response_data['image'] = l_img
			response_data['username'] = user_obj.username
			response_data['count'] = follow_count
			response_data['user_id'] = user_obj.id
			if notification_settings(user_obj.id, 'friends_accept_notify') == True:
				if not Notification.objects.filter(msg_type='friends_accepted', user=user_obj,
												   from_user=request.user).exists():
					Notification.objects.create(user=user_obj, from_user=request.user, msg_type='friends_accepted',
												message=f_nt_message)"""
	return json_response(response_data)


@login_required(login_url='/login')
def rejectFriendRequest(request):
	"""

	:param request:
	:return:
	"""
	response_data = {'result': False}
	if request.method == 'POST' and request.is_ajax():
		to_user_id = request.POST.get('to_user', '')
		response_data = remove_friend(request.user.id, to_user_id)
	return json_response(response_data)


@login_required(login_url='/login')
def newFriendRequest(request):
	"""

	:param request:
	:return:
	"""
	response_data = {'result': False, 'messages': 'Invitation sent Fail. Please try again later'}
	if request.method == 'POST' and request.is_ajax():
		email = request.POST.get('emails', None)
		response_data = invite_email_friend(request.user.id, email)
	return json_response(response_data)


def friendNotifications(request):
	"""

	:param request:
	:return:
	"""
	friend_list = []
	response_data = {'result': False, 'messages': ' Error into Notification'}
	friend_request_notification = None
	if request.method == 'GET' and request.is_ajax():
		response_data = get_friend_invite_notifications(request.user.id, data=request.GET)
	return json_response(response_data)


def friendNotificationsCount(request):
	"""

	:param request:
	:return:
	"""
	response_data = {'result': False, 'messages': ' Error into Notification count', 'count': 0}
	if request.method == 'GET' and request.is_ajax() and request.user.is_authenticated:
		response_data = get_friend_notifications_count(request.user.id)
	return json_response(response_data)


@login_required(login_url='/')
def friendssharesearch(request):
	"""
	   Share Skigit to Friends by Searching Username.
	"""
	search_list = []
	friends_list = []
	ski_share_list = []
	response_data = {'result': False, 'search_list': search_list}
	if request.method == 'POST' and request.is_ajax():
		search = request.POST.get('search_text', None)
		video_id = request.POST.get('video_id', None)
		time_zone = request.POST.get('time_zone', None)
		term = search.split()
		if len(term) > 2:
			response_data['result'] = True
		else:
			if len(search) != 0:
				if Friend.objects.filter(Q(from_user=request.user.id) | Q(to_user=request.user.id), status='1'):
					friends_object = Friend.objects.filter(Q(from_user=request.user.id) | Q(to_user=request.user.id),
														   status='1')
					from_user_list = friends_object.exclude(from_user__id=request.user.id).values_list('from_user__id',
																									   flat=True).distinct()
					to_user_list = friends_object.exclude(to_user__id=request.user.id).values_list('to_user__id',
																								   flat=True).distinct()
					friends_list = list(merge(from_user_list, to_user_list))
					friends_list = [friend for friend in friends_list if get_object_or_None(User, id=friend).profile.is_completed['status']]

					kwargs = {
						'first_name__istartswith': term[0],
						'id__in': friends_list,
						'is_active': True
					}
					if len(term) > 1:
						kwargs['last_name__istartswith'] = term[1]


				query_result = User.objects.exclude(id=request.user.id).filter(**kwargs).order_by('first_name')

				for qs in query_result:
					ps = Profile.objects.get(user=qs)
					share_obj = Share.objects.filter(skigit_id__id=video_id, is_active=True,
													 to_user=qs, user=request.user).last()
					if share_obj:
						share_date = get_time_delta(share_obj.created_date, time_zone),
					else:
						share_date = ''
					if ps.profile_img:
						#l_img = get_thumbnail(ps.profile_img, '24x24', quality=99, format='PNG').url
						l_img = api_request_images(ps.profile_img, quality=99, format='PNG')
					else:
						l_img = "{0}{1}".format(settings.STATIC_URL,'skigit/detube/images/noimage_user.jpg')
					search_list.append({'uid': qs.id,
										'username': qs.username,
										'name': qs.get_full_name(),
										'image': l_img,
										'share_date': share_date,
										'logged_in': True if qs.id in get_all_logged_in_users() else False})
					response_data['result'] = True
					response_data['search_list'] = sorted(map(dict, set(tuple(x.items()) for x in search_list)),
														  key=lambda k: k['name'])
			else:
				friend_list = []
				if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1).exists():
					f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id), status=1)
					from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user',
																						   flat=True).distinct()
					to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user', flat=True).distinct()
					fr_list = list(merge(from_user_list, to_user_list))
					fr_list = [friend for friend in fr_list if get_object_or_None(User, id=friend).profile.is_completed['status']]

					friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')
					for friends in friends_detail:
						share_obj = Share.objects.filter(skigit_id__id=video_id,
														 is_active=True,
														 to_user=friends.user,
														 user=request.user).order_by('to_user', '-pk').distinct('to_user')
						if share_obj:
							for sh in share_obj:
								share_date = get_time_delta(sh.created_date, time_zone),
						else:
							share_date = ''

						if friends.profile_img:
							#l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
							l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
						else:
							l_img = "{0}{1}".format(settings.STATIC_URL,'images/noimage_user.jpg')
						friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
											'name': friends.user.get_full_name(), 'image': l_img,
											'share_date': share_date,
											'logged_in': True if friends.user.id in get_all_logged_in_users() else False})
					response_data['result'] = True
					response_data['search_list'] = sorted(map(dict, set(tuple(x.items()) for x in friend_list)),
														  key=lambda k: k['name'])
	return json_response(response_data)


@login_required(login_url='/')
def share_skigit_date(request):
	"""
		Share Skigit View
	"""
	response_data = {'is_success': False, 'message': 'Error into ajax call of skigit record.'}
	if request.is_ajax() and request.method == 'POST':
		friend_list = []
		time_zone = request.POST.get('time_zone', None)
		video_id = request.POST.get('video_id', None)

		share_obj = Share.objects.exclude(
			to_user=request.user.id).filter(skigit_id__id=video_id, is_active=True, user=request.user.id
											).order_by('to_user', '-pk').distinct('to_user')
		if share_obj:
			for sh in share_obj:
				share_date = get_time_delta(sh.created_date, time_zone)
				friend_list.append({'id': sh.to_user.id, 'video_id': int(video_id), 'username': sh.to_user.username,
									'name': sh.user.get_full_name(), 'share_date': share_date})
			response_data['is_success'] = True
			response_data['message'] = 'Share dates found.'
			response_data['share_data'] = friend_list
		else:
			response_data['is_success'] = False
			response_data['message'] = 'Share dates not found.'
	return json_response(response_data)


def notifications_ajax(request):
	"""
		Notification Skigit. <Snapdragon Notification>
	"""
	response_data = {'is_success': False, 'message': 'Fail Error in to Notification Ajax Call'}
	if request.is_ajax() and request.method == 'POST':
		time_zone = request.POST.get('time_zone', '')
		notification_list = []
		plug_message = []
		parent_title = skigi_id = child_skigi_id = parent_skigi_id = child_title = None
		if Notification.objects.filter(user=request.user, is_read=False).exists():
			Notification.objects.filter(msg_type__icontains='_deleted').delete()
			start_date = datetime.now() - timedelta(days=30)
			end_date = datetime.now()
			Notification.objects.filter(user=request.user, is_read=False).update(is_view=True)
			notify_obj = Notification.objects.filter(user=request.user, created_date__range=(start_date, end_date),
													 is_read=False, is_active=True).order_by('-created_date')
			for notify in notify_obj:
				created_date = get_time_delta(notify.created_date, time_zone)
				if notify.skigit_id and Video.objects.filter(id=int(notify.skigit_id)).exists():
					video = Video.objects.get(id=int(notify.skigit_id))
					vid_title = video.title
					ski_id = notify.skigit_id
					if VideoDetail.objects.filter(skigit_id=int(notify.skigit_id)).exists():
						video_detail = VideoDetail.objects.filter(skigit_id=int(notify.skigit_id)).first()
						skigi_id = video_detail.id
				else:
					vid_title = None
					ski_id = None
				if notify.msg_type == 'plug_primary':
					if not (str(notify.message).find("*@p*")) == -1:
						plug_message = int((notify.message).split("*@p*")[-1])
						plug_detail = Video.objects.filter(id=int(plug_message)).values_list('title', flat=True)
						parent_title = plug_detail[0]
						video_de = VideoDetail.objects.get(title=plug_detail[0])
						parent_skigi_id = video_de.id
					elif not (str(notify.message).find("*@c*")) == -1:
						plug_message = int((notify.message).split("*@c*")[-1])
						plug_detail = Video.objects.filter(id=int(plug_message)).values_list('title', flat=True)
						child_title = plug_detail[0]
						video_de = VideoDetail.objects.get(title=plug_detail[0])
						child_skigi_id = video_de.id
					else:
						plug_message = None
				notification_list.append({'message': notify.message, 'user': notify.user.id, 'vid_title': vid_title,
										  'username': notify.user.username, 'from_user': notify.from_user.id,
										  'from_username': notify.from_user.username, 'is_read': notify.is_read,
										  'msg_type': notify.msg_type, 'skigit_id': ski_id, 'date': created_date,
										  'parent_title': parent_title, 'child_title': child_title,
										  'parent_child_id': plug_message, 'child_skigi_id': child_skigi_id,
										  'parent_skigi_id': parent_skigi_id, 'play_back_id': skigi_id})
			response_data['is_success'] = True
			response_data['message'] = 'Successfully get the notification list'
			response_data['notify_list'] = notification_list
		else:
			response_data['is_success'] = False
			response_data['message'] = 'No notifications to display!'
	return json_response(response_data)


def remove_notify_ajax(request):
	"""
	Delete Notification Skigit. <Snapdragon Notification Remove>
	:param request:
	:return:
	"""
	response_data = {'is_success': False, 'message': 'Fail Error in to Delete Notification Ajax Call'}

	if request.is_ajax() and request.method == 'POST':
		response_data = delete_notification(data=request.POST)
	return json_response(response_data)


def record_internal_embed(vid_id, from_id, to_id, request):
	response_data = {'is_success': False, 'message': 'Skigit failed to Embed in Profile Page. Please try again later'}
	if Video.objects.filter(id=vid_id).exists():
		video = Video.objects.get(id=vid_id)
		to_user = User.objects.get(pk=to_id)
		from_user = User.objects.get(pk=from_id)

		if not Embed.objects.filter(from_user=from_user, to_user=to_user,
									skigit_id=video, embed_type='0').exists():
			Embed.objects.create(from_user=from_user, to_user=to_user, skigit_id=video,
								 embed_count=1)
			response_data['is_success'] = True,
			response_data['message'] = 'Skigit Embed Successful'
		else:
			embed_id = Embed.objects.get(from_user=from_user, to_user=to_user, skigit_id=video, embed_type='0')
			Embed.objects.filter(from_user=from_user, to_user=to_user, skigit_id=video,
								 embed_type='0').update(is_embed=True,
														embed_count=int(embed_id.embed_count) + 1)
			response_data['is_success'] = True,
			response_data['message'] = 'Skigit Embed Successful'
		
		# create invoice
		response_data = business_internal_embed_fees(vid_id, request)
			
	return response_data


def internal_embed_ajax(request):
	"""
	Internal Embed
	:param request: Ajax Request Call
	:return: Embed Success Message
	"""
	response_data = {'is_success': False, 'message': 'Skigit failed to Embed in Profile Page. Please try again later'}
	try:
		if request.method == 'POST' and request.is_ajax():
			vid_id = int(request.POST.get('skigit_id', ''))
			from_id = int(request.POST.get('from_id', ''))
			to_id = int(request.POST.get('to_id', ''))

			response_data = record_internal_embed(vid_id, from_id, to_id, request)

	except Exception as exc:
		logger.error("Internal embed error ", exc)
	return json_response(response_data)


def remove_embed_ajax(request):
	"""
	Un Embed Skigit
	:param request:
	:return:
	"""
	response_data = {'is_success': False, 'message': 'Skigit failed to Embed in Profile Page. Please try again later'}
	if request.method == 'POST' and request.is_ajax():
		skigit_id = int(request.POST.get('skigit_id', None))
		video = VideoDetail.objects.get(id=skigit_id)
		Embed.objects.filter(to_user=request.user, skigit_id__id=video.skigit_id.id, embed_type='0').update(
			is_embed=False)
		response_data['is_success'] = False,
		response_data['message'] = 'successfully removed internal embed skigit'
	return json_response(response_data)


def age_calculator(birth_date):
	"""
		Age Calculator.
	"""
	age = (datetime.today().date() - birth_date).days / 365
	return age


def get_related_users(request, skigit_user_id, *argv):
	"""
		Returns the Relative Skigits on the basis of category,
		 subcategory, gender, and Age.
	"""
	user_list = []
	if Profile.objects.filter(user__id=request.user.id).exists():
		profile_dic = Profile.objects.get(user__id=request.user.id)
		user_gender = profile_dic.gender
		current_age = int(age_calculator(profile_dic.birthdate))
		user_profile = Profile.objects.filter(Q(gender=user_gender) | Q(user__id=int(skigit_user_id)))
		for profile in user_profile:
			if profile.birthdate and profile.birthdate.year <= datetime.now().year:
				age = int(age_calculator(profile.birthdate))
				if 1 <= age < 5 and 1 <= current_age < 5:
					user_list.append(profile.user.id)
				elif 5 <= age <= 12 and 5 <= current_age <= 12:
					user_list.append(profile.user.id)
				elif 13 <= age <= 18 and 13 <= current_age <= 18:
					user_list.append(profile.user.id)
				elif 19 <= age <= 26 and 19 <= current_age <= 26:
					user_list.append(profile.user.id)
				elif 27 <= age <= 35 and 27 <= current_age <= 35:
					user_list.append(profile.user.id)
				elif 36 <= age <= 45 and 36 <= current_age <= 45:
					user_list.append(profile.user.id)
				elif 46 <= age <= 55 and 46 <= current_age <= 55:
					user_list.append(profile.user.id)
				elif 56 <= age <= 65 and 56 <= current_age <= 65:
					user_list.append(profile.user.id)
				elif age > 65 and current_age > 65:
					user_list.append(profile.user.id)

		if not user_list:
			years_ago_date = profile_dic.birthdate - timedelta(days=(65 * 365))
			user_list = Profile.objects.filter(gender=user_gender, birthdate__gt=years_ago_date,
											   birthdate__lt=profile_dic.birthdate).values_list('user__id', flat=True)
	return user_list


def make_wall_post(request):
	user = request.user
	poster = None
	profile = Profile.objects.get(user=request.user)
	if WallPoster.objects.exists():
		wall_post = WallPoster.objects.all()[0]
		skigit_logo = request.build_absolute_uri(wall_post.skigit_logo.url)
		header_image = request.build_absolute_uri(wall_post.header_image.url)
		poster_1 = request.build_absolute_uri(wall_post.poster_1.url)
		poster_2 = request.build_absolute_uri(wall_post.poster_2.url)
		if PosterBusinessLogo.objects.filter(user=request.user).exists():
			if PosterBusinessLogo.objects.filter(user=request.user, wall_post=wall_post).exists():
				poster = PosterBusinessLogo.objects.get(user=request.user, wall_post=wall_post)
			else:
				PosterBusinessLogo.objects.filter(user=request.user).update(wall_post=wall_post)
				poster = PosterBusinessLogo.objects.get(user=request.user, wall_post=wall_post)
		else:
			if profile.logo_img.exists():
				b_logo_url = profile.logo_img.filter(is_deleted=False)[0].logo
			PosterBusinessLogo.objects.create(user=request.user, wall_post=wall_post,
											  b_logo=request.build_absolute_uri(b_logo_url.url))
			poster = PosterBusinessLogo.objects.filter(user=request.user, wall_post=wall_post)
		if PosterBusinessLogo.objects.filter(user=request.user, wall_post=wall_post).exists():
			poster_obj = PosterBusinessLogo.objects.get(user=request.user, wall_post=wall_post)
	return locals()

@login_required(login_url='/')
def set_wall_poster(request):
	"""
		Update business Logo for Wall poster and Brochures View
	"""
	response_data = {'is_success': False, 'message': 'Error into set user poster image.. try later!'}
	try:
		if request.is_ajax() and request.method == 'POST':
			wall_poster = PosterBusinessLogo.objects.get(user=request.user)
			if wall_poster:
				file = request.POST.get('file', None)
				unique_key = round(datetime.now().timestamp())
				name = 'wallPoster_' + str(unique_key) + '.png'
				data = ContentFile(base64.b64decode(file), name=name)
				wall_poster.poster_img.delete(save=True)
				wall_poster.poster_img = data
				wall_poster.save()
				response_data['is_success'] = True
				response_data['message'] = 'User wall poster set successfully'
		else:
			response_data['is_success'] = False
			response_data['message'] = 'Setting wall poster failed, No wall poster found'
	except Exception as e:
		response_data['is_success'] = False
		response_data['message'] = e.message

	return json_response(response_data)

@login_required(login_url='/')
@xframe_options_exempt
@payment_required
@require_filled_profile
def wall_post_skigit24x36(request):
	"""
		Skigit Wall Poster View for size 24x36
	"""
	context = make_wall_post(request)
	return render(request, 'brochure/brochure24x36.html', context)


@login_required(login_url='/')
@xframe_options_exempt
@payment_required
@require_filled_profile
def wallpaper_print(request):
	"""
		Skigit Wall Poster View for size 18x24
	"""
	context = make_wall_post(request)
	return render(request, 'brochure/wallpaperiframe.html', context)


@login_required(login_url='/')
@payment_required
@require_filled_profile
def wall_poster_preview(request):
	"""
		Wall Poster Preview
	"""
	user = request.user
	facebook_app_id= settings.FACEBOOK_APP_ID
	poster = None
	wall_post_exists = False
	profile = Profile.objects.get(user=request.user)
	if WallPoster.objects.exists():
		wall_post_exists = True
		wall_post = WallPoster.objects.all()[0]
		skigit_logo = request.build_absolute_uri(wall_post.skigit_logo.url)
		header_image = request.build_absolute_uri(wall_post.header_image.url)
		poster_1 = request.build_absolute_uri(wall_post.poster_1.url)
		poster_2 = request.build_absolute_uri(wall_post.poster_2.url)
		if PosterBusinessLogo.objects.filter(user=request.user).exists():
			if PosterBusinessLogo.objects.filter(user=request.user, wall_post=wall_post).exists():
				poster = PosterBusinessLogo.objects.get(user=request.user, wall_post=wall_post)
			else:
				PosterBusinessLogo.objects.filter(user=request.user).update(wall_post=wall_post)
				poster = PosterBusinessLogo.objects.get(user=request.user, wall_post=wall_post)
		else:
			if profile.logo_img.exists():
				b_logo_url = profile.logo_img.filter(is_deleted=False)[0].logo
			PosterBusinessLogo.objects.create(user=request.user, wall_post=wall_post,
											  b_logo=request.build_absolute_uri(b_logo_url.url))
			poster = PosterBusinessLogo.objects.filter(user=request.user, wall_post=wall_post)
		if PosterBusinessLogo.objects.filter(user=request.user, wall_post=wall_post).exists():
			poster_obj = PosterBusinessLogo.objects.get(user=request.user, wall_post=wall_post)
			poster_img = request.build_absolute_uri(poster_obj.poster_img.url) if poster_obj.poster_img else ""


			
	return render(request, 'brochure/wallpreview.html', locals())


@login_required(login_url='/')
def get_b_logo(request):
	"""
		Get business Logo for Wall poster and Brochures View
	"""
	all_business_logo = []
	try:
		profile = Profile.objects.filter(user=request.user)
		for prof in profile:
			if prof.logo_img.filter(is_deleted=False).all():
				all_logo_obj = prof.logo_img.filter(is_deleted=False).all()
				for l_obj in all_logo_obj:
					tmp = [l_obj.id, request.build_absolute_uri(l_obj.logo.url)]
					all_business_logo.append(tmp)
					del tmp
		data = {'all_business_logo': all_business_logo}
	except Exception as e:
		data = {'error': e.message, 'all_business_logo': all_business_logo}

	return HttpResponse(json.dumps(data), content_type="application/json")


@login_required(login_url='/')
def set_b_logo(request):
	response_data = {'is_success': False, 'message': 'Error into set new logo to wall post.. try later!'}
	if request.is_ajax() and request.method == 'POST':
		logo_url = request.POST.get('b_logo', None)
		if logo_url:
			PosterBusinessLogo.objects.filter(user=request.user).update(b_logo=logo_url)
			response_data['is_success'] = True
			response_data['message'] = 'New Logo set successfully'
		else:
			response_data['is_success'] = False
			response_data['message'] = 'New logo set failed. Image not Found'
	return json_response(response_data)


@login_required(login_url='/')
def set_brochure_logo(request):
	"""
		Update business Logo for Wall poster and Brochures View
	"""
	response_data = {'is_success': False, 'message': 'Error into set new logo to wall post.. try later!'}
	if request.is_ajax() and request.method == 'POST':
		logo_url = request.POST.get('b_logo', None)
		if logo_url:
			BrochureBLogo.objects.filter(user=request.user).update(b_logo=logo_url)
			response_data['is_success'] = True
			response_data['message'] = 'New Logo set successfully'
		else:
			response_data['is_success'] = False
			response_data['message'] = 'New logo set failed . Image not Found'
	return json_response(response_data)

@login_required(login_url='/')
def set_brochure(request):
	"""
		Update business Logo for Wall poster and Brochures View
	"""
	response_data = {'is_success': False, 'message': 'Error into set new logo to wall post.. try later!'}
	try:
		if request.is_ajax() and request.method == 'POST':
			brochure = BrochureBLogo.objects.get(user=request.user)
			if brochure:
				file = request.POST.get('file', None)
				unique_key = round(datetime.now().timestamp())
				name = 'brochure_' + str(unique_key)  + '.png'
				data = ContentFile(base64.b64decode(file), name=name)
				brochure.poster_img.delete(save=True)
				brochure.poster_img = data
				brochure.save()
				response_data['is_success'] = True
				response_data['message'] = 'User wall poster set successfully'
			else:
				response_data['is_success'] = False
				response_data['message'] = 'Setting wall poster failed, No wall poster found'
	except Exception as e:
		response_data['is_success'] = False
		response_data['message'] = e.message
	return json_response(response_data)


@login_required(login_url='/')
@payment_required
@require_filled_profile
def brochure_preview(request):
	"""
		 Brochures Preview View
	"""
	user = request.user
	facebook_app_id = settings.FACEBOOK_APP_ID
	profile = Profile.objects.get(user=request.user)
	brochure_exists = False
	if Brochure.objects.exists():
		brochure_exists = True
		brochure = Brochure.objects.all()[0]
		poster_1 = request.build_absolute_uri(brochure.poster_1.url)
		if BrochureBLogo.objects.filter(user=request.user).exists():
			if BrochureBLogo.objects.filter(user=request.user, brochure=brochure).exists():
				poster = BrochureBLogo.objects.get(user=request.user, brochure=brochure)
			else:
				BrochureBLogo.objects.filter(user=request.user).update(brochure=brochure)
				poster = BrochureBLogo.objects.get(user=request.user, brochure=brochure)
		else:
			#profile = Profile.objects.get(user=request.user)
			if profile.logo_img.exists():
				b_logo_url = profile.logo_img.filter(is_deleted=False)[0].logo
				BrochureBLogo.objects.create(user=request.user, brochure=brochure,
											 b_logo=request.build_absolute_uri(b_logo_url.url))
			poster = BrochureBLogo.objects.filter(user=request.user, brochure=brochure)
		if BrochureBLogo.objects.filter(user=request.user, brochure=brochure).exists():
			poster_obj = BrochureBLogo.objects.get(user=request.user, brochure=brochure)
			poster_img = request.build_absolute_uri(poster_obj.poster_img.url) if poster_obj.poster_img else ""
		host = ''.join(settings.HOST)[:-1]
		meta = Meta(
				image=poster_img,
				image_width=600,
				image_height=500,
				url=host + '/friends/brochure-print/',
				use_og=True,
				object_type="website",
				use_facebook=True,
				use_twitter=True,
				facebook_app_id= settings.FACEBOOK_APP_ID
			)
		share_url = meta.url
	return render(request, 'brochure/viewbrochure.html', locals())


@xframe_options_exempt
def brochure_print(request):
	"""
		Brochures Print Template View
	"""

	user = request.user
	brochure_exists = False
	profile = Profile.objects.get(user=request.user)
	if Brochure.objects.exists():
		brochure_exists = True
		brochure = Brochure.objects.all()[0]
		poster_1 = request.build_absolute_uri(brochure.poster_1.url)
		if BrochureBLogo.objects.filter(user=request.user).exists():
			if BrochureBLogo.objects.filter(user=request.user, brochure=brochure).exists():
				poster = BrochureBLogo.objects.get(user=request.user, brochure=brochure)
			else:
				BrochureBLogo.objects.filter(user=request.user).update(brochure=brochure)
				poster = BrochureBLogo.objects.get(user=request.user, brochure=brochure)
		else:
			if profile.logo_img.exists():
				b_logo_url = profile.logo_img.filter(is_deleted=False)[0].logo
				BrochureBLogo.objects.create(user=request.user, brochure=brochure,
											 b_logo=request.build_absolute_uri(b_logo_url.url))
			poster = BrochureBLogo.objects.filter(user=request.user, brochure=brochure)
		if BrochureBLogo.objects.filter(user=request.user, brochure=brochure).exists():
			poster_obj = BrochureBLogo.objects.get(user=request.user, brochure=brochure)
	return render(request, 'brochure/brochureiframe.html', locals())


def get_friends_list(user_id='',
					 search_query=''):
	'''

	:param user_id:
	:param search_query:
	:return: Friends list
	'''

	friends_list = []
	result = []

	if user_id:
		friends_object = Friend.objects.filter(Q(from_user__id=user_id) | Q(to_user__id=user_id),
											   status='1')
		if friends_object.exists():

			from_user_list = friends_object.exclude(from_user__id=user_id).values_list('from_user__id',
																					   flat=True).distinct()
			to_user_list = friends_object.exclude(to_user__id=user_id).values_list('to_user__id',
																				   flat=True).distinct()
			friends_list = list(merge(from_user_list, to_user_list))
	else:
		friends_list = User.objects.filter(is_active=True).values_list('id', flat=True)

	friends_list = [friend for friend in friends_list if
					get_object_or_None(User, id=friend).profile.is_completed['status']]

	term = search_query.split()
	if len(term) <= 2 and search_query != '':
		kwargs = {
			'is_active':True
		}
		kwargs['first_name__istartswith'] = term[0].strip()
		if len(term) > 1:
			kwargs['last_name__istartswith'] = term[1].strip()

		query_result = User.objects.filter(**kwargs)

		result.extend(query_result.values_list('id', flat=True))

	# for term in search_query.split():
	#     term = term.strip()
	#     query_result = User.objects.filter(
	#                     Q(first_name__icontains=term) | Q(last_name__icontains=term) |
	#                       Q(email=term) | Q(username__icontains=term),
	#                     is_active=True)
	#     result.extend(query_result.values_list('id', flat=True))

	if search_query:
		if user_id and result.count(int(user_id)) > 1:
			result.remove(int(user_id))
		if friends_list:
			result = set(friends_list) & set(result)
	else:
		result.extend(friends_list)

	result = list(set(result))
	profile_objs = Profile.objects.filter(user__id__in=result).order_by('user__username')
	return profile_objs

class ProfileFriendsInviteAPIView(generics.RetrieveAPIView):
	serializer_class = ProfileFriendsInviteSerializer
	permission_classes = (CustomIsAuthenticated,)

	def get(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.query_params
		user_id = request.user.id if request.auth else 0
		search_query = data.get('search_query', '').strip()

		try:
			response_data = get_friends_invite_search_result(user_id, search=search_query, api_request=True)
			page = self.paginate_queryset(response_data['search_list'] if 'search_list' in response_data else [])
			if page != None:
				serializer = self.get_serializer(page, many=True)
				paginated_result = self.get_paginated_response(serializer.data)
				result.update(status='success',
							  message='',
							  data=paginated_result.data)

		except Exception as exc:
			logger.error("Serializer: ProfileFriendsInviteAPIView:", exc)
			result.update(status='error',
						  message='Friends are not loaded. Please try again.')
		return Response(result)

class FriendInviteInternalAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.data
		user_id = request.user.id if request.auth else 0
		to_user_id = data.get('to_user', '')
		response_data = invite_friend_internal(user_id, to_user_id)
		result.update(status='success' if response_data['result'] else 'error',
					  message=response_data['message'] if response_data['message'] else '')
		return Response(result)

class FriendInviteEmailAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.data
		user_id = request.user.id if request.auth else 0
		email = data.get('email', '')
		try:
			response_data = invite_email_friend(user_id, email)
			result.update(status='success' if response_data['result'] else 'error',
						  message=response_data['messages'] if response_data['messages'] else '')
		except Exception as exc:
			logger.error("Serializer: FriendsInvite Email APIView:", exc)
			result.update(status='error',
						  message='Friend invite via email throws error. Please try again.')
		return Response(result)

class FriendAcceptAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.data
		user_id = request.user.id if request.auth else 0
		to_user_id = data.get('to_user', '')
		try:
			response_data = accept_friend(user_id, to_user_id, api_request=True)
			result.update(status='success' if response_data['result'] else 'error',
						  message=response_data['message'] if 'message' in response_data and response_data['message'] else '')
			for i in ['message', 'result']:
				if i in response_data:
					response_data.pop(i)
			result.update(data=response_data)
		except Exception as exc:
			logger.error("Serializer: Friend Accept APIView:", exc)
			result.update(status='error',
						  message='Friend accept throws error. Please try again.')
		return Response(result)

class FriendRemoveAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.data
		user_id = request.user.id if request.auth else 0
		to_user_id = data.get('to_user', '')
		try:
			response_data = remove_friend(user_id, to_user_id)
			result.update(status='success' if response_data['result'] else 'error',
						  message=response_data['message'] if response_data['message'] else '')
		except Exception as exc:
			logger.error("Serializer: Friend Remove APIView:", exc)
			result.update(status='error',
						  message='Friend remove throws error. Please try again.')
		return Response(result)

class FriendInviteNotificationsAPIView(generics.ListAPIView):
	serializer_class = FriendNotificationsAPISerializer
	permission_classes = (CustomIsAuthenticated,)

	def get(self, request):
		result = {'status': '',
				  'message': ''}
		result_data = {}
		data = request.query_params
		user_id = request.user.id if request.auth else 0
		try:
			response_data = get_friend_invite_notifications(user_id, data, api_request=True)
			if response_data['friend_list']:
				friends = response_data['friend_list']
				page = self.paginate_queryset(friends)

				if page != None:
					serializer = self.get_serializer(page, many=True)
					paginated_result = self.get_paginated_response(serializer.data)
					result_data = paginated_result.data
				else:
					serializer = self.get_serializer(friends, many=True)
					result_data = serializer.data
			result.update(status='success',
						  message=response_data['messages'] if response_data['messages'] else '',
						  data=result_data)
		except Exception as exc:
			logger.error("Serializer: Friend Invite Notification API :", exc)
			result.update(status='error',
						  message='Error when loading the friend notifications. Please try again.')
		return Response(result)

class GeneralNotificationsAPIView(generics.ListAPIView):
	serializer_class = GeneralNotificationsAPISerializer
	permission_classes = (CustomIsAuthenticated,)

	def get(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.query_params.copy()
		user_id = request.user.id if request.auth else 0
		data.update(user_id=user_id)

		try:
			response_data = get_general_notifications(data)

			if 'notify_list' in response_data:
				notifications = response_data['notify_list']
				page = self.paginate_queryset(notifications)


				if page != None:
					# serializer = self.get_serializer(page, many=True)
					paginated_result = self.get_paginated_response(notifications)
					data = paginated_result.data
				else:
					# serializer = self.get_serializer(notifications, many=True)
					data = notifications
			result.update(status='success',
						  message=response_data['message'],
						  data=data)
		except Exception as exc:
			logger.error("Serializer: General Notification API :", exc)
			result.update(status='error',
						  message='Error when loading general notifications. Please try again.')
		return Response(result)

class NotificationCountAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def get(self, request):
		result = {'status': '',
				  'message': ''}
		response_data = {}
		data = request.query_params.copy()
		user_id = request.user.id if request.auth else 0
		data.update(user_id=user_id)

		try:
			response_data.update(general_notifications=get_general_notifications_count(user_id))
			response_data.update(friend_notifications=get_friend_notifications_count(user_id))
			result.update(status='success',
						  data=response_data)
		except Exception as exc:
			logger.error("Serializer: Notification Count API :", exc)
			result.update(status='error',
						  message='Error when loading notification count. Please try again.')
		return Response(result)

class ReadNotificationAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.data.copy()
		user_id = request.user.id if request.auth else 0
		data.update(user_id=user_id)

		try:
			response_data = read_notification(data)
			result.update(status='success' if response_data['is_success'] else 'error',
						  message=response_data['message'] if response_data['message'] else '')
		except Exception as exc:
			logger.error("Serializer: Read Notification API :", exc)
			result.update(status='error',
						  message='Error when reading notification. Please try again.')
		return Response(result)

class DeleteNotificationAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		result = {'status': '',
				  'message': ''}
		data = request.data.copy()
		user_id = request.user.id if request.auth else 0
		data['to_user'] = user_id
		logger.info("DATA: %s", data)

		if 'skigit_id' in data and int(data['skigit_id']) != 0:
			data['skigit_id'] = VideoDetail.objects.get(id=int(data['skigit_id'])).skigit_id.id

		try:
			response_data = delete_notification(data)
			result.update(status='success' if response_data['is_success'] else 'error',
						  message=response_data['message'] if response_data['message'] else '')
		except Exception as exc:
			logger.error("Serializer: Delete Notification API :", exc)
			result.update(status='error',
						  message='Error when deleting notification. Please try again.')
		return Response(result)


class SkigitInternalEmbedFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				  'message': ''}
		data = request.data.copy()
		vid_id = data.get('skigit_id', None)
		from_id = data.get('from_id', None)
		to_id = data.get('to_id', None)
		try:
			response_data = record_internal_embed(vid_id, from_id, to_id, request)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit internal embed fee error", exc)
			response_data.update(status="error",\
				message='Error in to Internal Embed Invoice! Try again Later or Contact to Administrator.')

		response_data.pop('is_success', None)
		return Response(response_data)