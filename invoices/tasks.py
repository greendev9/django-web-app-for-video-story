# Create your tasks here
from __future__ import absolute_import, unicode_literals
from time import sleep
from celery import shared_task

from django.conf import settings
from constance import config

from core.utils import is_user_business
from mailpost.models import EmailTemplate
from invoices.models import Invoice, MonthlySkigitInvoice, MonthlyLogoInvoice
from skigit.models import VideoDetail
from user.models import User, Profile
import datetime
from decimal import Decimal

@shared_task
def monthly_invoice():

	if config.SENT_MONTHLY_INVOICE:
		invoices = Invoice.objects.filter(type__in=['CreditCard',
													'PayPalAccount'],
										  is_deleted=False)
		for i in invoices:
			if is_user_business(i.user):
				EmailTemplate.send(
					template_key="monthly_invoice",
					emails=[i.user.email],
					context={
						"invoice_link": "{0}/profile/invoice/".format(settings.HOST),
						"username": i.user.username,
      					"host": ''.join(settings.HOST)[:-1]
						}
				)
				sleep(10)
	return ()

#
# @shared_task
# def create_monthly_skigit_and_logo_invoice(): # for monthly skigits and logos as with new months
#
# 	current_month = datetime.datetime.now().date().month
# 	current_year = datetime.datetime.now().date().year
# 	business_user = User.objects.filter(groups__name=settings.BUSINESS_USER,
# 										invoice_user__type__in=['PayPalAccount', 'CreditCard'],
# 										invoice_user__is_deleted=False
# 										).distinct('username')
#
# 	business_profile = Profile.objects.filter(user__id__in=business_user.values_list('id', flat=True),
# 											  payment_method__isnull=False,
# 											  payment_email__isnull=False)
#
# 	for profile in business_profile:
# 		# for monthly skigits
# 		skigits = VideoDetail.objects.select_related('skigit_id').filter(
# 			skigit_id__user=profile.user, status=1, is_active=True)
#
# 		existing_record = MonthlySkigitInvoice.objects.filter(user=profile.user,
# 															  billing_month__month=current_month,
# 															  billing_month__year=current_year
# 															  )
# 		if not existing_record.exists():
# 			MonthlySkigitInvoice.objects.create(user=profile.user,
# 												billing_month=datetime.datetime.now().date(),
# 												skigit_amount=config.FEE_BUSINESS_SKIGIT_MONTHLY_MAINTENANCE,
# 												total_skigit_count=skigits.count(),
# 												skigit_total_amount=skigits.count() * Decimal(config.FEE_BUSINESS_SKIGIT_MONTHLY_MAINTENANCE)
# 												)
#
# 		# for monthly logo
# 		logos = profile.logo_img.filter(is_deleted=False)
# 		existing_record = MonthlyLogoInvoice.objects.filter(user=profile.user,
# 															  billing_month__month=current_month,
# 															  billing_month__year=current_year
# 															)
# 		if not existing_record.exists():
# 			MonthlyLogoInvoice.objects.create(user=profile.user, billing_month=datetime.datetime.now().date(),logo_amount=config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY,total_logo_count=logos.count(),logo_total_amount=logos.count() * Decimal(config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY))
#
# 	return ()