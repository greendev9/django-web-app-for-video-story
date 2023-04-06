# Create your tasks here
from celery import shared_task
from user.models import Profile, User
from skigit.models import CopyRightInfringement
from datetime import timedelta, datetime
from django.utils import timezone
from core.utils import (get_user_type, check_if_last_day_of_month,)
from invoices.views import manage_pay_invoice
import logging
from constance import config

logger = logging.getLogger('Skigit')

@shared_task
def delete_user_account_content():
	logger.info("Delete account / Clear invoice script started")

	date_before_thirty_days = timezone.now() - timedelta(days=config.DAYS_COUNT_FOR_AUTO_DELETE_BOT)
  
	# delete general user straight forward
	profiles = Profile.objects.filter(deactivated_at__lte=date_before_thirty_days, user__is_active=False)\
		.select_related('user').prefetch_related('user__groups').prefetch_related('user__infringement_copytight_user')

	user_ids_to_be_deleted = []
	for profile in profiles:
		# check if any copy right claim
		if profile.user.infringement_copytight_user.exclude(status__in=[2,3]).exists():
			continue

		if get_user_type(profile.user) == 'business':
			# clear current month invoice if today is last day of month
			if check_if_last_day_of_month(datetime.today()):
				resp = manage_pay_invoice(profile.user.id, {
					'month': datetime.today().month,
					'year': datetime.today().year
				})
				# no further action if invoice clearance fails
				if not resp['is_success']:
					continue

		user_ids_to_be_deleted.append(profile.user.id)

	User.objects.filter(id__in=user_ids_to_be_deleted).delete()

	logger.info("Delete account / Clear invoice script end")

	return ()



