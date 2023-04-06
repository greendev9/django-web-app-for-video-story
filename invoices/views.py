import ast
import datetime
from decimal import Decimal
from operator import itemgetter
import logging

import braintree
from Crypto import Random
from Crypto.PublicKey import RSA
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.models import User
from rest_framework import views, generics
from rest_framework.response import Response
from mailpost.models import EmailTemplate

from user.models import BusinessLogo, Profile, ProfileUrl
from core.utils import (json_response, payment_required, is_user_business,
						get_object_or_None, CustomIsAuthenticated, get_client_token)
from invoices.models import *
# Create your views here.
from skigit_project import settings
from .serializers import InvoiceDetailSerializer
from constance import config

logger = logging.getLogger('Invoices')

if settings.PROD:
  braintree.Configuration.configure(
			braintree.Environment.Production,
			merchant_id=settings.BRAINTREE_MERCHANT_ID,
			public_key=settings.BRAINTREE_PUBLIC_KEY,
			private_key=settings.BRAINTREE_PRIVATE_KEY
	)
else:
  braintree.Configuration.configure(
			braintree.Environment.Sandbox,
			merchant_id=settings.BRAINTREE_MERCHANT_ID,
			public_key=settings.BRAINTREE_PUBLIC_KEY,
			private_key=settings.BRAINTREE_PRIVATE_KEY
	)


def get_payment_methods(user):
		"""
		:param user:
		:return: Get all payment active methods of an user!
		"""

		payment_methods = []
		paypal_account = Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False)
		card_account = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=False)
		if paypal_account.exists():
				inv = paypal_account.first()
				card_type = inv.type
				card_detail = inv.email
				card_img = inv.c_image_url
				payment_methods.append({'card_type': card_type, 'card_detail': card_detail,
																'card_img': card_img, 'inv': inv, 'default_account': user.profile.payment_method == '0'})
		if card_account.exists():
				inv = card_account.first()
				card_type = inv.type
				card_detail = str('%06d*****%04d') % (int(inv.first_6), int(inv.last_4))
				card_img = inv.c_image_url
				payment_methods.append({'card_type': card_type, 'card_detail': card_detail,
																'card_img': card_img, 'inv': inv, 'default_account': user.profile.payment_method == '1'})
		return payment_methods


def get_payment_customer_token(user, method_type):
		"""
				Get a customer token and ID!
				*method_type: 'CreditCard'/'PayPalAccount'
		"""
		result = {}
		invoice_obj = Invoice.objects.filter(user=user, type=method_type, is_deleted=False).first()

		if invoice_obj:
				if invoice_obj.customer_id:
						result.update(customer_id=invoice_obj.customer_id)
				if invoice_obj.payment_method_token:
						result.update(customer_token=invoice_obj.payment_method_token)
		result.update(client_token=get_client_token(user))
		return result


@staticmethod
def get_rsa_encryption(card_detail, bits=2048):
		"""
				RSA Algorithm For Create Encrypted Private and Public key
		"""
		random_generator = Random.new().read
		key = RSA.generate(bits, random_generator)
		public_key = key.publickey()  # pub key export for exchange
		encrypted = public_key.encrypt(card_detail, 128)
		# message to encrypt is in the above line 'encrypt this message'
		decrypted = key.decrypt(ast.literal_eval(str(encrypted)))
		return encrypted


def get_rsa_decryption(m):
		"""
				RSA Algorithm For Create Decryption Private and Public key
		"""
		pass


def business_logo_fees(logo, request):
	response_data = {'is_success': False,
					'message': 'Error in to Business logo Invoice! Try again Later or Contact to Administrator.'}

	busniesslogo = BusinessLogo.objects.get(id=int(logo), is_deleted=False)
	profile = Profile.objects.get(logo_img=busniesslogo)
	if is_user_business(profile.user):
			current_month = datetime.datetime.now().date().month
			current_year = datetime.datetime.now().date().year
		
			if not profile.user.username == request.user.username:
					if not BusinessLogoInvoice.objects.filter(user=request.user, logo_user=profile.user,
															  billing_month__month=current_month,
															  # business_logo=busniesslogo,
															  billing_month__year=current_year).exists():

							existing_record = BusinessLogoInvoice.objects.filter(logo_user=profile.user,
																															 billing_month__month=current_month,
																															 billing_month__year=current_year
																															 ).order_by('-id')

							if existing_record.exists():
								last_record = existing_record.first()
								total_count = last_record.total_logo_count + Decimal(1)
								total_amount = last_record.user_total_due + Decimal(config.FEE_LOGO_CLICK)
							else:
								total_count = 1
								total_amount = config.FEE_SOCIAL_NETWORK_POST

							logo_invoice = BusinessLogoInvoice.objects.create(user=request.user, 
																								logo_user=profile.user, 
																								logo_count=1,
																								billing_month=datetime.datetime.now().date(),
																								business_logo=busniesslogo,
																								logo_total_amount=config.FEE_LOGO_CLICK,
																								total_logo_count=total_count,
																								user_total_due=total_amount
																							)

							response_data['is_success'] = True
							response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
																				 % (str(logo_invoice.billing_month.month), str(total_count),
																						str(total_amount))
					else:

							existing_record = BusinessLogoInvoice.objects.filter(user=request.user, logo_user=profile.user,
																								 billing_month__month=datetime.datetime.now().date().month,
																								 billing_month__year=datetime.datetime.now().date().year
																								 ).order_by('-id')

							last_record = existing_record.first()
							last_record.total_logo_count += Decimal(1)
							last_record.user_total_due += Decimal(config.FEE_LOGO_CLICK)
							last_record.logo_count += Decimal(1)
							last_record.logo_total_amount += Decimal(config.FEE_LOGO_CLICK)
							last_record.save()

							response_data['is_success'] = True
							response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
																				 % (str(last_record.billing_month.month), str(last_record.total_logo_count), str(last_record.user_total_due))
			else:
					response_data['is_success'] = True
					response_data['message'] = 'Logo is uploaded by Current user- Charges are Not applicable'
	else:
			response_data['is_success'] = True
			response_data['message'] = ' %s is general user - (Note: Payment Not Applicable to General User)' \
																 % request.user.username
	return response_data

@csrf_protect
def business_logo_invoice(request):
	"""
			Business Logo Invoice
	"""
	response_data = {'is_success': False, 'message': 'Business Logo Error. Submit this bug to the Skigit Administrator. Thank you!'}

	if request.is_ajax() and request.method == 'POST':

		logo = request.POST.get('logo_id', None)
		response_data = business_logo_fees(logo, request)
	return json_response(response_data)


def weblink_fees(web_user, web_url, request):
	response_data = {'is_success': False,
					'message': 'Error in to Weblink Invoice! Try again Later or Contact to Administrator.'}

	profile = ProfileUrl.objects.get(user__id=int(web_user))
	if is_user_business(profile.user):
			current_month = datetime.datetime.now().date().month
			current_year = datetime.datetime.now().date().year

			if not profile.user.username == request.user.username:
					if not WebLinkInvoice.objects.filter(user=request.user, web_link_user=profile.user, web_link=web_url,
																							 billing_month__month=current_month,
																							 billing_month__year=current_year).exists():

							existing_record = WebLinkInvoice.objects.filter(user=request.user, web_link_user=profile.user, web_link=web_url,
																						billing_month__month=current_month, billing_month__year=current_year
																						).order_by('-id')

							if existing_record.exists():
								last_record = existing_record.first()
								total_count = last_record.link_total_count + Decimal(1)
								total_amount = last_record.link_total_due + Decimal(config.FEE_WEBSITE_LINKS_CLICK)
							else:
								total_count = 1
								total_amount = config.FEE_WEBSITE_LINKS_CLICK

							weblink_invoice = WebLinkInvoice.objects.create(user=request.user,
																						web_link_user=profile.user,
																						web_link=web_url,
																						billing_month=datetime.datetime.now().date(),
																						link_count=1,
																						link_due_amount=config.FEE_WEBSITE_LINKS_CLICK,
																						link_total_count=total_count,
																						link_total_due=total_amount
																					)

							response_data['is_success'] = True
							response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
																				 % (str(weblink_invoice.billing_month.month), str(total_count),
																						str(total_amount))
					else:

							existing_record = WebLinkInvoice.objects.filter(user=request.user,
																						billing_month__month=current_month, billing_month__year=current_year
																						).order_by('-id')

							last_record = existing_record.first()
							last_record.link_total_count += Decimal(1)
							last_record.link_total_due += Decimal(config.FEE_WEBSITE_LINKS_CLICK)

							weblink_invoice = WebLinkInvoice.objects.get(user=request.user, web_link_user=profile.user,
																												web_link=web_url, billing_month__month=current_month,
																												billing_month__year=current_year)

							weblink_invoice.link_count += Decimal(1)
							weblink_invoice.link_due_amount += Decimal(config.FEE_WEBSITE_LINKS_CLICK)

							weblink_invoice.link_total_count += Decimal(1)
							weblink_invoice.link_total_due += Decimal(config.FEE_WEBSITE_LINKS_CLICK)

							last_record.save()
							weblink_invoice.save()


							response_data['is_success'] = True
							response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
																				 % (str(last_record.billing_month.month), str(last_record.link_total_count), str(last_record.link_total_due))
			else:
					response_data['is_success'] = True
					response_data['message'] = 'Web Link is uploaded by Current user- Charges are Not applicable'
	else:
			response_data['is_success'] = True
			response_data['message'] = ' %s is general user - (Note: Payment Not Applicable to General User)' \
																			 % profile.user.username
	return response_data																		 
												

@csrf_protect
def business_weblink_invoice(request):
		"""
				Business Web Link Invoice
		"""
		response_data = {'is_success': False, 'message': 'Error in to Web Link Invoice! Try again Later'
																										 ' or Contact to Administrator'}
		if request.is_ajax() and request.method == 'POST':
				web_user = request.POST.get('link_user', None)
				web_url = request.POST.get('web_link', None)
				response_data = weblink_fees(web_user, web_url, request)

		return json_response(response_data)


def learn_more_fees(login_id, skigit_id, request):
	response_data = {'is_success': False,
					'message': 'Error in to Learn More Invoice! Try again Later or Contact to Administrator.'}

	skigit = VideoDetail.objects.get(skigit_id_id=int(skigit_id))
	profile = Profile.objects.get(user=skigit.skigit_id.user)

	current_month = datetime.datetime.now().date().month
	current_year = datetime.datetime.now().date().year
	# charge skigit logo user

	if skigit.made_by and is_user_business(skigit.made_by):
		if not LearnMoreInvoice.objects.filter(user=skigit.made_by, learn_ski=skigit,
											   billing_month__month=current_month,
											   billing_month__year=current_year).exists():

			existing_record = LearnMoreInvoice.objects.filter(user=skigit.made_by, billing_month__month=current_month,
															  billing_month__year=current_year
															  ).order_by('-id')

			if existing_record.exists():
				last_record = existing_record.first()
				total_count = last_record.learn_total_count + Decimal(1)
				total_amount = last_record.learn_total_due + Decimal(config.FEE_LEARN_MORE)
			else:
				total_count = 1
				total_amount = config.FEE_LEARN_MORE

			learn_invoice = LearnMoreInvoice.objects.create(user=skigit.made_by,
															learn_ski=skigit,
															billing_month=datetime.datetime.now().date(),
															learn_count=1,
															learn_due_amount=config.FEE_LEARN_MORE,
															learn_total_count=total_count,
															learn_total_due=total_amount,
															learn_total_amount=total_amount,
															)

			response_data['is_success'] = True
			response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
									   % (str(learn_invoice.billing_month.month), str(total_count),
										  str(total_amount))
		else:

			existing_record = LearnMoreInvoice.objects.filter(user=skigit.made_by,
															  billing_month__month=current_month,
															  billing_month__year=current_year
															  ).order_by('-id')

			last_record = existing_record.first()
			last_record.learn_total_count += Decimal(1)
			last_record.learn_total_amount += Decimal(config.FEE_LEARN_MORE)
			last_record.learn_total_due += Decimal(config.FEE_LEARN_MORE)

			learn_invoice = LearnMoreInvoice.objects.get(user=skigit.made_by, learn_ski=skigit,
														 billing_month__month=current_month,
														 billing_month__year=current_year)

			learn_invoice.learn_count += Decimal(1)
			learn_invoice.learn_due_amount += Decimal(config.FEE_LEARN_MORE)

			learn_invoice.learn_total_count += Decimal(1)
			learn_invoice.learn_total_amount += Decimal(config.FEE_LEARN_MORE)
			learn_invoice.learn_total_due += Decimal(config.FEE_LEARN_MORE)

			last_record.save()
			learn_invoice.save()

			response_data['is_success'] = True
			response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
									   % (str(last_record.billing_month.month), str(last_record.learn_total_count),
										  str(last_record.learn_total_amount))
	else:
		response_data['is_success'] = True
		response_data['message'] = ' %s is general user - (Note: Payment Not Applicable to General User)' \
								   % profile.user.username

	# charge skigit owner
	if is_user_business(profile.user) and profile.user != skigit.made_by:
		if not profile.user.username == request.user.username:
				if not LearnMoreInvoice.objects.filter(user=profile.user, learn_ski=skigit,
																							 billing_month__month=current_month,
																							 billing_month__year=current_year).exists():


						existing_record = LearnMoreInvoice.objects.filter(user=profile.user, billing_month__month=current_month, billing_month__year=current_year
																					 ).order_by('-id')

						if existing_record.exists():
							last_record = existing_record.first()
							total_count = last_record.learn_total_count + Decimal(1)
							total_amount = last_record.learn_total_due + Decimal(config.FEE_LEARN_MORE)
						else:
							total_count = 1
							total_amount = config.FEE_LEARN_MORE

						learn_invoice = LearnMoreInvoice.objects.create(user=profile.user,
																					learn_ski=skigit,
																					billing_month=datetime.datetime.now().date(),
																					learn_count=1,
																					learn_due_amount=config.FEE_LEARN_MORE,
																					learn_total_count=total_count,
																					learn_total_due=total_amount,
																					learn_total_amount=total_amount,
																				)


						response_data['is_success'] = True
						response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
																			 % (str(learn_invoice.billing_month.month), str(total_count),
																					str(total_amount))
				else:

						existing_record = LearnMoreInvoice.objects.filter(user=profile.user,
																						billing_month__month=current_month, billing_month__year=current_year
																					 ).order_by('-id')

						last_record = existing_record.first()
						last_record.learn_total_count += Decimal(1)
						last_record.learn_total_amount += Decimal(config.FEE_LEARN_MORE)
						last_record.learn_total_due += Decimal(config.FEE_LEARN_MORE)

						learn_invoice = LearnMoreInvoice.objects.get(user=profile.user, learn_ski=skigit,
																												 billing_month__month=current_month,
																												 billing_month__year=current_year)

						learn_invoice.learn_count += Decimal(1)
						learn_invoice.learn_due_amount += Decimal(config.FEE_LEARN_MORE)

						learn_invoice.learn_total_count += Decimal(1)
						learn_invoice.learn_total_amount += Decimal(config.FEE_LEARN_MORE)
						learn_invoice.learn_total_due += Decimal(config.FEE_LEARN_MORE)

						last_record.save()
						learn_invoice.save()

						response_data['is_success'] = True
						response_data['message'] = "Current Month %s's Count %s and Due Amount is:%s" \
																			 % (str(last_record.billing_month.month), str(last_record.learn_total_count), str(last_record.learn_total_amount))
		else:
				response_data['is_success'] = True
				response_data['message'] = 'Learn More is uploaded by Current user- Charges are Not applicable'
	else:
		response_data['is_success'] = True
		response_data['message'] = ' %s is general user - (Note: Payment Not Applicable to General User)' \
																	 % profile.user.username
	return response_data

@csrf_protect
def business_learn_more_invoice(request):
	""" Learn More Link Invoice
	"""
	response_data = {'is_success': False, 'message': 'Error in to Learn More Link Invoice! Try again Later'
																									 ' or Contact to Administrator'}
	if request.is_ajax() and request.method == 'POST':
		login_id = request.POST.get('login_id', None)
		skigit_id = request.POST.get('skigit_id', None)
		response_data = learn_more_fees(login_id, skigit_id, request)

	return json_response(response_data)


def business_post_fees(ski_user, ski_id, social_type, request):
	response_data = {'is_success': False,
					'message': 'Error in to Business Post Invoice! Try again Later or Contact to Administrator.'}

	vid_obj = VideoDetail.objects.get(skigit_id__id=int(ski_id))

	current_month = datetime.datetime.now().date().month
	current_year = datetime.datetime.now().date().year
	current_date = datetime.datetime.now().date()

	if vid_obj.made_by:
			l_user = vid_obj.made_by
			if not l_user == request.user.username and is_user_business(l_user):
					request_user = request.user
					if str(request_user) == "AnonymousUser":
						request_user = None
					if not PostInvoice.objects.filter(user=request_user, post_ski=vid_obj, logo_user=l_user,
																						social_network_type=social_type, billing_month__month=current_month,
																						billing_month__year=current_year).exists():

							existing_record = PostInvoice.objects.filter(logo_user=l_user, billing_month__month=current_month,
																				 billing_month__year=current_year).order_by('-id')

							if existing_record.exists():
								last_record = existing_record.first()
								total_count = last_record.post_total_count + Decimal(1)
								total_amount = last_record.post_total_amount + Decimal(config.FEE_SOCIAL_NETWORK_POST)
							else:
								total_count = 1
								total_amount = config.FEE_SOCIAL_NETWORK_POST

							post_invoice = PostInvoice.objects.create(user=request_user,
																				logo_user=l_user, post_ski=vid_obj,
																				billing_month=current_date,
																				social_network_type=social_type,
																				post_count=1,
																				skigit_post_amount=config.FEE_SOCIAL_NETWORK_POST,
																				post_total_count=total_count,
																				post_total_amount=total_amount,
																			)

							response_data['is_success'] = True
							response_data['message'] = "Social Post Current Month %s's Count %s and Due Amount is:%s" % \
																				 (str(post_invoice.billing_month.month), str(total_count), str(total_amount))
					else:

							existing_record = PostInvoice.objects.filter(logo_user=l_user, billing_month__month=current_month,
																				 billing_month__year=current_year).order_by('-id')

							last_record = existing_record.first()
							last_record.post_total_count += Decimal(1)
							last_record.post_total_amount += Decimal(config.FEE_SOCIAL_NETWORK_POST)


							post_invoice = PostInvoice.objects.get(user=request_user, post_ski=vid_obj,
																										 logo_user=l_user,
																										 social_network_type=social_type,
																										 billing_month__month=current_month,
																										 billing_month__year=current_year)

							post_invoice.post_count += Decimal(1)
							post_invoice.skigit_post_amount += Decimal(config.FEE_SOCIAL_NETWORK_POST)

							post_invoice.post_total_count += Decimal(1)
							post_invoice.post_total_amount += Decimal(config.FEE_SOCIAL_NETWORK_POST)

							last_record.save()
							post_invoice.save()

						 
							response_data['is_success'] = True
							response_data['message'] = "Social Post Current Month %s's Count %s and Due Amount is:%s" \
																				 % (str(last_record.billing_month.month), str(last_record.post_total_count), str(last_record.post_total_amount))
			else:
					response_data['is_success'] = True
					response_data['message'] = 'Skigit is property of Current user/ General user -' \
																		 ' Charges are not applicable.'
	return response_data

@csrf_protect
def business_post_invoice(request):
		"""
				Business Post Invoice
		"""
		response_data = {'is_success': False, 'message': 'Error in to Post Invoice! Try again Later '
																										 'or Contact to Administrator.'}
		if request.is_ajax() and request.method == 'POST':
				ski_user = request.POST.get('skigit_user', None)
				ski_id = request.POST.get('skigit_id', None)
				social_type = request.POST.get('social_type', None)
				response_data = business_post_fees(ski_user, ski_id, social_type, request)
		return json_response(response_data)


def business_plug_invoice(request, plug_ski, plugin_user, ski_id, logo_user):
		"""
				Business Plug-in Invoice
		"""
		response_data = {'is_success': False,
										 'message': 'Error in to Post Invoice! Try again Later or Contact to Administrator.'}

		b_logo_user = User.objects.get(pk=int(logo_user))
		plug_user = User.objects.get(pk=int(plugin_user))
		vid_obj = VideoDetail.objects.get(id=int(ski_id))
		plug_obj = VideoDetail.objects.get(id=int(plug_ski))
		current_month = datetime.datetime.now().date().month
		current_year = datetime.datetime.now().date().year
		current_date = datetime.datetime.now().date()

		if not b_logo_user == plug_user and is_user_business(b_logo_user):
			if not PluginInvoice.objects.filter(user=plug_user, skigit_user=b_logo_user, primary_ski=plug_obj,
																					plugin_ski=vid_obj, billing_month__month=current_month,
																					billing_month__year=current_year).exists():
					existing_record = PluginInvoice.objects.filter(skigit_user=b_logo_user, billing_month__month=current_month,
																			 billing_month__year=current_year).order_by('-id')

					if existing_record.exists():
						last_record = existing_record.first()
						total_count = last_record.plugin_total_count + Decimal(1)
						total_amount = last_record.plugin_total_amount + Decimal(config.FEE_SKIGIT_PLUGIN)
					else:
						total_count = 1
						total_amount = config.FEE_SKIGIT_PLUGIN

					plug_invoice = PluginInvoice.objects.create(user=plug_user, 
																			skigit_user=b_logo_user,
																			plugin_ski=vid_obj, 
																			primary_ski=plug_obj,
																			billing_month=current_date,
																			plugin_count=1,
																			current_plugin_amount=config.FEE_SKIGIT_PLUGIN,
																			plugin_total_count=total_count,
																			plugin_total_amount=total_amount,
																)

					response_data['is_success'] = True
					response_data['message'] = "Social Post Current Month %s's Count %s and Due Amount is:%s" % \
																		 (str(plug_invoice.billing_month.month), str(total_count), str(total_amount))
			else:

					existing_record = PluginInvoice.objects.filter(skigit_user=b_logo_user, billing_month__month=current_month,
																			 billing_month__year=current_year).order_by('-id')

					last_record = existing_record.first()
					last_record.plugin_total_count += Decimal(1)
					last_record.plugin_total_amount += Decimal(config.FEE_SKIGIT_PLUGIN)


					plug_invoice = PluginInvoice.objects.get(user=plug_user, plugin_ski=vid_obj, primary_ski=plug_obj,
																									 skigit_user=b_logo_user, billing_month__month=current_month,
																									 billing_month__year=current_year)

					plug_invoice.plugin_count += Decimal(1)
					plug_invoice.current_plugin_amount += Decimal(config.FEE_SKIGIT_PLUGIN)

					plug_invoice.plugin_total_count += Decimal(1)
					plug_invoice.plugin_total_amount += Decimal(config.FEE_SKIGIT_PLUGIN)

					last_record.save()
					plug_invoice.save()

					response_data['is_success'] = True
					response_data['message'] = "Social Post Current Month %s's Count %s and Due Amount is:%s" \
																		 % (str(last_record.billing_month.month),
																				str(last_record.plugin_total_count), str(last_record.plugin_total_amount))
		else:
			response_data['is_success'] = True
			response_data['message'] = 'Skigit is property of Current user/ General user -' \
																 ' Charges are not applicable.'

		return json_response(response_data)


def business_share_invoice(visit_user, ski_id):
		"""
				Business Share Invoice
		"""
		response_data = {'is_success': False,
										 'message': 'Error in to Share Invoice! Try again Later or Contact to Administrator.'}
		v_user = User.objects.get(pk=int(visit_user))
		vid_obj = VideoDetail.objects.get(skigit_id__id=int(ski_id))
		current_month = datetime.datetime.now().date().month
		current_year = datetime.datetime.now().date().year
		current_date = datetime.datetime.now().date()

		if vid_obj.made_by:
				logo_user = vid_obj.made_by
				if is_user_business(logo_user):
					if not ShareInvoice.objects.filter(user=v_user, skigit_user=logo_user, share_ski=vid_obj,
																						 billing_month__month=current_month,
																						 billing_month__year=current_year).exists():

							existing_record = ShareInvoice.objects.filter(skigit_user=logo_user, billing_month__month=current_month,
																					billing_month__year=current_year).order_by('-id')

							if existing_record.exists():
								last_record = existing_record.first()
								total_count = last_record.total_share_count + Decimal(1)
								total_amount = last_record.share_total_amount + Decimal(config.FEE_SKIGIT_SHARE)
							else:
								total_count = 1
								total_amount = config.FEE_SKIGIT_SHARE

							share_invoice = ShareInvoice.objects.create(user=v_user,
																					skigit_user=logo_user, 
																					share_ski=vid_obj,
																					billing_month=current_date, 
																					share_count=1,
																					skigit_share_amount=config.FEE_SKIGIT_SHARE,
																					total_share_count=total_count,
																					share_total_amount=total_amount

															)
							response_data['is_success'] = True
							response_data['message'] = "Share Current Month %s's Count %s and Due Amount is:%s" % \
																				 (str(share_invoice.billing_month.month), str(total_count), str(total_amount))
					else:
							existing_record = ShareInvoice.objects.filter(skigit_user=logo_user, billing_month__month=current_month,
																					billing_month__year=current_year).order_by('-id')

							last_record = existing_record.first()
							last_record.total_share_count += Decimal(1)
							last_record.share_total_amount += Decimal(config.FEE_SKIGIT_SHARE)


							share_invoice = ShareInvoice.objects.get(user=v_user, share_ski=vid_obj, skigit_user=logo_user,
																											 billing_month__month=current_month,
																											 billing_month__year=current_year)

							share_invoice.share_count += Decimal(1)
							share_invoice.skigit_share_amount += Decimal(config.FEE_SKIGIT_SHARE)

							share_invoice.total_share_count += Decimal(1)
							share_invoice.share_total_amount += Decimal(config.FEE_SKIGIT_SHARE)

							last_record.save()
							share_invoice.save()
						 
							response_data['is_success'] = True
							response_data['message'] = "Share Current Month %s's Count %s and Due Amount is: %s" \
																				 % (str(last_record.billing_month.month), str(last_record.total_share_count), str(last_record.share_total_amount))
		return json_response(response_data)


def business_embed_fees(ski_id, request):

	response_data = {'is_success': False,
					'message': 'Error in to Business Embed Invoice! Try again Later or Contact to Administrator.'}

	vid_obj = VideoDetail.objects.get(id=int(ski_id))
	user = vid_obj.skigit_id.user

	current_month = datetime.datetime.now().date().month
	current_year = datetime.datetime.now().date().year
	current_date = datetime.datetime.now().date()
	if is_user_business(request.user):
		if not EmbedInvoice.objects.filter(
				user=request.user,
				skigit_user=user,
				embed_ski=vid_obj,
				billing_month__month=current_month, billing_month__year=current_year
				).exists():

				# fetch last record as it contains the total amount and total count so far
				existing_record = EmbedInvoice.objects.filter(
						user=request.user,
						billing_month__month=current_month,
						billing_month__year=current_year
				).order_by('-id')

				if existing_record.exists():
					last_record = existing_record.first()
					total_count = last_record.embed_total_count + Decimal(1)
					total_amount = last_record.embed_total_amount + Decimal(config.FEE_SKIGIT_EMBED_MY_SITE)
				else:
					total_count = 1
					total_amount = config.FEE_SKIGIT_EMBED_MY_SITE

				embed_invoice = EmbedInvoice.objects.create(
						user=request.user, skigit_user=user,
						embed_ski=vid_obj,
						billing_month=current_date,
						embed_count=1,
						skigit_embed_amount=config.FEE_SKIGIT_EMBED_MY_SITE,
						embed_total_count=total_count,
						embed_total_amount=total_amount,
				)

				response_data['is_success'] = True
				response_data['message'] = "Social Post Current Month %s's Count %s and Due Amount is:%s" % \
																	 (str(embed_invoice.billing_month.month), str(embed_invoice.embed_total_count), str(embed_invoice.embed_total_amount))
		else:
				response_data['is_success'] = True
				response_data['message'] = "Already charges are apply for %s skigit for Current Month." % vid_obj.title

	return response_data


@csrf_protect
def business_embed_invoice(request):
	"""
			Business Embed Invoice
	"""
	response_data = {'is_success': False,
									 'message': 'Error in to Embed Invoice! Try again Later or Contact to Administrator'}

	if request.is_ajax() and request.method == 'POST':
		ski_id = request.POST.get('skigit_id', None)
		response_data = business_embed_fees(ski_id, request)
	return json_response(response_data)


def business_internal_embed_fees(ski_id, request):
	response_data = {'is_success': False,
					'message': 'Error in to Business Internal Bembed Invoice! Try again Later or Contact to Administrator.'}

	vid_obj = VideoDetail.objects.get(skigit_id=int(ski_id))

	current_month = datetime.datetime.now().date().month
	current_year = datetime.datetime.now().date().year
	current_date = datetime.datetime.now().date()
	if is_user_business(request.user):
			if not InternalEmbedInvoice.objects.filter(
							skigit_user=request.user,
							user=vid_obj.skigit_id.user,
							embed_ski=vid_obj,
							billing_month__month=current_month,
							billing_month__year=current_year
					).exists():
					# fetch last record as it contains the total amount and total count so far

					existing_record = InternalEmbedInvoice.objects.filter(
							skigit_user=request.user,
							billing_month__month=current_month,
							billing_month__year=current_year
					).order_by('-id')

					if existing_record.exists():
						last_record = existing_record.first()
						total_count = last_record.embed_total_count + Decimal(1)
						total_amount = last_record.embed_total_amount + Decimal(config.FEE_SKIGIT_INTERNEL_EMBED)
					else:
						total_count = 1
						total_amount = config.FEE_SKIGIT_INTERNEL_EMBED


					embed_invoice = InternalEmbedInvoice.objects.create(
							skigit_user=request.user,
							user=vid_obj.skigit_id.user,
							embed_ski=vid_obj,
							billing_month=current_date,
							embed_count=1,
							skigit_embed_amount=config.FEE_SKIGIT_INTERNEL_EMBED,
							embed_total_count=total_count,
							embed_total_amount=total_amount
					)

					response_data['is_success'] = True
					response_data['message'] = "Social Post Current Month %s's Count %s and Due Amount is:%s" % \
																		 (str(embed_invoice.billing_month.month), str(embed_invoice.embed_total_count), str(embed_invoice.embed_total_amount))
			else:
					response_data['is_success'] = True
					response_data['message'] = "Already charges are apply for %s skigit for Current Month." % vid_obj.title
	return response_data


# @csrf_protect
# def business_internal_embed_invoice(request):
# 	"""
# 			Business Internal Embed Invoice
# 	"""
# 	response_data = {'is_success': False,
# 									 'message': 'Error in to Internal Embed Invoice! Try again Later or Contact to Administrator'}

# 	if request.is_ajax() and request.method == 'POST':
# 		ski_id = request.POST.get('skigit_id', None)
# 		response_data = business_internal_embed_fees(ski_id, request)
	
# 	return json_response(response_data)


def skigit_view_fees(skigit_id, view_page, request):
	response_data = {}
	current_month = datetime.datetime.now().date().month
	current_year = datetime.datetime.now().date().year
	current_date = datetime.datetime.now().date()

	vid_obj = VideoDetail.objects.get(id=int(skigit_id))
	if request.user.is_authenticated:
		user = request.user
	else:
		user = None

	if vid_obj.made_by:

			logo_user = vid_obj.made_by
			if not logo_user == user and is_user_business(logo_user):
				view_fee = config.FEE_MAIN_SKIGIT_VIEW if view_page == 1 else config.FEE_SKIGIT_VIEW

				if not ViewInvoice.objects.filter(skigit_user=logo_user, view_ski=vid_obj,
												  billing_month__month=current_month,
												  billing_month__year=current_year,
												  view_page=view_page).exists():

						existing_record = ViewInvoice.objects.filter(skigit_user=logo_user, billing_month__month=current_month,
																				billing_month__year=current_year, view_page=view_page).order_by('-id')

						if existing_record.exists():
							last_record = existing_record.first()
							total_count = last_record.total_view_count + Decimal(1)
							total_amount = last_record.view_total_amount + Decimal(view_fee)
						else:
							total_count = 1
							total_amount = view_fee

						view_invoice = ViewInvoice.objects.create(user=user,
																  skigit_user=logo_user,
																  view_ski=vid_obj,
																  billing_month=current_date,
																  view_count=1,
																  skigit_view_amount=view_fee,
																  total_view_count=total_count,
																  view_total_amount=total_amount,
																  view_page=view_page)
						response_data.update(is_success=True,
											 message="Social Post Current Month {}'s Count {} and Due Amount is:{}".format(view_invoice.billing_month.month,
																														   total_count,
																														   total_amount))
				else:
						existing_record = ViewInvoice.objects.filter(skigit_user=logo_user, billing_month__month=current_month,
																	 billing_month__year=current_year, view_page=view_page).order_by('-id')

						last_record = existing_record.first()
						last_record.total_view_count += Decimal(1)
						last_record.view_total_amount += Decimal(view_fee)

						view_invoice = ViewInvoice.objects.get(view_ski=vid_obj, skigit_user=logo_user,
															   billing_month__month=current_month,
															   billing_month__year=current_year, view_page=view_page)

						view_invoice.view_count += Decimal(1)
						view_invoice.skigit_view_amount += Decimal(view_fee)

						view_invoice.total_view_count += Decimal(1)
						view_invoice.view_total_amount += Decimal(view_fee)

						last_record.save()
						view_invoice.save()
						response_data.update(is_success=True,
											 message="Social Post Current Month {}'s Count {} and Due Amount is: {}".format(last_record.billing_month.month,
																															last_record.total_view_count,
																															last_record.view_total_amount))
	return response_data

@csrf_protect
def skigit_view_invoice(request):
		"""
				Business View Invoice
		"""
		response_data = {'is_success': False,
						 'message': 'Error: View Invoice! Try again later or contact Administrator'}

		data = request.POST

		skigit_id = data.get('skigit_id', None)
		view_page = data.get('view_page', 0)

		videoDetail = VideoDetail.objects.get(id=skigit_id, status=1)

		if videoDetail:
			videoDetail.view_count = videoDetail.view_count + 1
			videoDetail.save()
		response_data = skigit_view_fees(skigit_id, view_page, request)

		return json_response(response_data)


def get_total_payable_amount(request):
		pass


def find_customer(request, token):
		"""
				Fined Customer Already Set in Braintree Vault.

		Args:
				request: request method
				token: Customer token
		"""
		customer = braintree.CreditCard.find(token)
		return customer


def find_pay_pal_customer(request, token):
		"""
				Find Paypal Account Customer

		Args:
				request: request method
				token: customer token
		"""
		customer = braintree.PaymentMethod.find(token)
		return customer

@csrf_protect
def customer_create(request):
		"""
				Braintree Vault Customer create
		"""
		response_data = {'is_success': False, 'message': 'Invalid Card details'}
		if request.is_ajax() and request.method == 'POST':
				user_id = request.user.id
				data = request.POST
				response_data = create_payment_customer(user_id, data, request=request)
		return json_response(response_data)


@csrf_protect
def pay_pal_customer_create(request):
		"""
				Braintree Vault Customer create
		"""

		response_data = {'is_success': False, 'message': 'Invalid Card details'}
		if request.is_ajax() and request.method == 'POST':
				user_id = request.user.id
				data = request.POST
				response_data = create_paypal_payment_customer(user_id, data, request=request)
		return json_response(response_data)


def payment_method_remove(request):
		"""
				Payment Account Removal function

				Args:
						request: Request method
		"""
		response_data = {'is_success': False, 'message': 'Error into removing card/paypal details.'}
		if request.method == 'POST' and request.is_ajax():
				data = request.POST
				response_data = delete_payment_type(request.user.id, data)
		return json_response(response_data)


def paypal_form(request):
	payment_environment = 'production' if settings.PROD else 'sandbox'
	return render(request, 'payment/paypal_form.html', locals())


def payment_invoice(request):
	return render(request, 'payment/invoice_card.html', locals())


@login_required(login_url='/login')
@payment_required
@csrf_exempt
def invoice_payment(request):
		"""
		Skigit Invoice Detail View
		"""
		user = request.user
		data = request.GET
		year = data.get('year', 0)
		month = int(data.get('month', 0))
		month_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
									'October', 'November', 'December']
		business_invoices_list = []
		year_list = range(user.date_joined.year, datetime.datetime.now().year + 1)

		if not year:
				year = datetime.datetime.now().year
		month = datetime.datetime.now().month
		if not int(year) == datetime.datetime.now().year:
				if int(month) == 1:
						year = int(year) - 1
				month = 12
		date = datetime.date(int(year), month, 1)

		payment_methods = get_payment_methods(user)

		if user.date_joined.year == year:
				start_range = user.date_joined.month
		else:
				start_range = 1
		for i in range(start_range, month + 1 if not int(year) == datetime.datetime.now().year else month + 1):
				b_learn_more_users, b_logo_users, b_link_users, b_plug_users, \
				b_post_users, b_share_users, b_embed_users, \
				total_amount, payment_recived, b_internel_embed_users, b_view_users, b_home_view_users,\
				b_monthly_logo, b_monthly_skigit, b_donate_skigit, b_qr_code = invoice_total_amount(user, month=i, year=year)

				if b_donate_skigit:
					total_amount_obj = b_donate_skigit.aggregate(total_amount=Sum('donate_amount'))
					donate_skigit_total_amount = total_amount_obj['total_amount']
					donate_skigit_count = b_donate_skigit.count()
				else:
					donate_skigit_total_amount, donate_skigit_count = 0, 0

				payment_info = {
						'current_month': datetime.datetime.now().month,
						'year': year,
						'month': month_list[i - 1],
						'month_num': i,
						'total_amount': total_amount,
						'learn_more_detail': b_learn_more_users.first(),
						'logo_detail': b_logo_users.first(),
						'link_detail': b_link_users.first(),
						'plug_detail': b_plug_users.first(),
						'post_detail': b_post_users.first(),
						'share_detail': b_share_users.first(),
						'embed_detail': b_embed_users.first(),
						'view_detail': b_view_users.first(),
						'monthly_logo_detail': b_monthly_logo.first(),
						'monthly_logo_fee': config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY,
						'monthly_skigit_detail': b_monthly_skigit.first(),
						'home_view_detail': b_home_view_users.first(),
						'internel_embed_detail': b_internel_embed_users.first(),
						'donate_skigit_detail': {'total_count': donate_skigit_count, 'total_amount': donate_skigit_total_amount},
						'qr_code_detail': b_qr_code.first(),
						'payment_recived': payment_recived.exists(),
						'transaction_id': payment_recived.first().transaction_id if payment_recived.exists() else None,
						'transaction_date': payment_recived.first().created_date.strftime(
								"%b %d, %Y") if payment_recived.exists() else None,
						'card_type': payment_recived.first().invoice.type if payment_recived.exists() else None,
						'card_img': payment_recived.first().invoice.c_image_url if payment_recived.exists() else None,
						'inv': payment_recived.first().invoice if payment_recived.exists() else None,
						'card_detail': str('%06d*****%04d') % (int(payment_recived.first().invoice.first_6),
																									 int(payment_recived.first().invoice.last_4))
						if payment_recived.exists() and payment_recived.first().invoice.type == 'CreditCard' else
						payment_recived.first().invoice.email if payment_recived.exists() else None
				}

				business_invoices_list.append(payment_info)
		business_invoices_list = sorted(business_invoices_list, key=itemgetter('month_num'), reverse=True)
		return render(request, 'profile/payment_invoices.html', locals())


@payment_required
def paybills(request):
		"""
				Paying Bill Method.
		"""
		response_data = {'is_success': False, 'message': 'Error into Paying bill, please contact administrator'}
		if request.method == 'POST' and request.is_ajax():
				response_data = manage_pay_invoice(user_id=request.user.id, data=request.POST)
		return json_response(response_data)


def invoice_total_amount(user, month, year=None):
		total_amount = Decimal(0.0)
		b_learn_more_users = LearnMoreInvoice.objects.filter(Q(user__username=user), billing_month__year=year,
																												 billing_month__month=month).order_by('-id')
		b_logo_users = BusinessLogoInvoice.objects.filter(Q(logo_user__username=user), billing_month__year=year,
																											billing_month__month=month).order_by('-id')
		b_link_users = WebLinkInvoice.objects.filter(Q(web_link_user__username=user), billing_month__year=year,
																								 billing_month__month=month).order_by('-id')
		b_plug_users = PluginInvoice.objects.filter(Q(skigit_user__username=user), billing_month__year=year,
																								#billing_month__month=date_value)
																								billing_month__month=month).order_by('-id')
		b_post_users = PostInvoice.objects.filter(Q(logo_user__username=user),
																							billing_month__month=month, billing_month__year=year).order_by('-id')
		b_share_users = ShareInvoice.objects.filter(Q(skigit_user__username=user), billing_month__year=year,
																								billing_month__month=month).order_by('-id')
		b_embed_users = EmbedInvoice.objects.filter(Q(user__username=user), billing_month__year=year,
																								billing_month__month=month).order_by('-id')

		b_internel_embed_users = InternalEmbedInvoice.objects.filter(Q(skigit_user__username=user), billing_month__year=year,
																								billing_month__month=month).order_by('-id')
		b_view_users = ViewInvoice.objects.filter(Q(skigit_user__username=user), billing_month__year=year,
																								billing_month__month=month, view_page=0).order_by('-id')
		b_home_view_users = ViewInvoice.objects.filter(Q(skigit_user__username=user), billing_month__year=year,
																								billing_month__month=month, view_page=1).order_by('-id')
		b_monthly_logo = MonthlyLogoInvoice.objects.filter(Q(user__username=user), billing_month__year=year,
													   billing_month__month=month).order_by('-id')
		b_monthly_skigit = MonthlySkigitInvoice.objects.filter(Q(user__username=user), billing_month__year=year,
														   billing_month__month=month).order_by('-id')
		b_donate_skigits = DonateInvoice.objects.filter(Q(user__username=user), billing_month__year=year,
													   billing_month__month=month).order_by('-id')
		b_qr_code = QRCodeInvoice.objects.filter(Q(user__username=user), billing_month__year=year,
													   billing_month__month=month).order_by('-id')

		if b_logo_users:
				total_amount += b_logo_users[0].user_total_due
		if b_learn_more_users:
				total_amount += b_learn_more_users[0].learn_total_amount
		if b_link_users:
				total_amount += b_link_users[0].link_total_due
		if b_plug_users:
				total_amount += b_plug_users[0].plugin_total_amount
		if b_post_users:
				total_amount += b_post_users[0].post_total_amount
		if b_share_users:
				total_amount += b_share_users[0].share_total_amount
		if b_embed_users:
				total_amount += b_embed_users[0].embed_total_amount
		if b_internel_embed_users:
				total_amount += b_internel_embed_users[0].embed_total_amount
		if b_view_users:
				total_amount += b_view_users[0].view_total_amount
		if b_home_view_users:
				total_amount += b_home_view_users[0].view_total_amount
		if b_monthly_logo:
				total_amount += b_monthly_logo[0].logo_total_amount
		else:
				total_amount += Decimal(config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY)
		if b_monthly_skigit:
				total_amount += b_monthly_skigit[0].skigit_total_amount
		if b_donate_skigits:
			total_amount_obj = b_donate_skigits.aggregate(total_amount=Sum('donate_amount'))
			total_amount += total_amount_obj['total_amount']

		if b_qr_code:
				total_amount += b_qr_code[0].qrcode_amount

		payment_recived = InvoiceBilling.objects.filter(user_id=user, pay_yr=year, pay_mnth=month)

		return (b_learn_more_users, b_logo_users, b_link_users, b_plug_users, b_post_users,
						b_share_users, b_embed_users, total_amount, payment_recived, b_internel_embed_users,
						b_view_users, b_home_view_users, b_monthly_logo, b_monthly_skigit, b_donate_skigits,b_qr_code)


def send_manual_invoice(request):
		result = {}

		if request.method == 'POST':
				data = request.POST
				try:
						user_ids = set(data['invoices'].replace(' ', '').split(','))
						users = User.objects.filter(id__in=user_ids)
						for user in users:
								EmailTemplate.send(
										template_key="monthly_invoice",
										emails=[user.email],
										context={
												"invoice_link": "{0}/profile/invoice/".format(settings.HOST),
												"username": user.username,
            									"host": ''.join(settings.HOST)[:-1]
										}
								)
						result.update(result='success')
				except:
						result.update(result='failure')
		return json_response(result)


# Generic functions

def manage_pay_invoice(user_id, data):
		inv = None
		user = get_object_or_None(User, id=user_id)
		response_data = {'is_success': False, 'message': 'Error into Paying bill, please contact administrator'}

		if user:
				if data.get('inv_id', None):
						inv = get_object_or_None(Invoice, id=data['inv_id'])
				else:
						profile_obj = get_object_or_None(Profile, user=user)
						if profile_obj.payment_method == '0':
								inv = Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False).first()
						elif profile_obj.payment_method == '1':
								inv = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=False).first()

		if inv:
				amount = data.get('amount', 0)
				month = data.get('month', 0)
				year = data.get('year', 0)
				# can't believe on user input amount - calculate now
				b_learn_more_users, b_logo_users, b_link_users, b_plug_users, b_post_users, b_share_users,\
				b_embed_users, total_amount, payment_recived, b_internel_embed_users, b_view_users, b_home_view_users,\
				b_monthly_logo, b_monthly_skigit, b_donate_skigit, b_qr_code = invoice_total_amount(user, month, year)

				amount = round(total_amount, 2)

				if InvoiceBilling.objects.filter(user_id=user, invoice=inv, pay_amount=amount,
																				 payed_amount=Decimal(amount), pay_yr=year, pay_mnth=month).exists():
						response_data = {'is_success': True, 'message': 'Payment is already received.'}
						return response_data

				result = braintree.Transaction.sale({
						"amount": amount,
						"payment_method_token": inv.payment_method_token,
						"customer_id": inv.customer_id,
						"options": {
								"submit_for_settlement": True,
						}
				})

				if result.is_success:

						pay_method = None
						if inv.type == 'PayPalAccount':
								pay_method = '0'
						elif inv.type == 'CreditCard':
								pay_method = '1'

						InvoiceBilling.objects.create(user_id=user, invoice=inv, pay_amount=amount,
																					payed_amount=Decimal(result.transaction.amount), pay_yr=year,
																					pay_mnth=month, transaction_id=result.transaction.id,
																					pay_method=pay_method, payment_status=True,
																					created_date=datetime.datetime.now())

						# update invoices as paid
						b_learn_more_users.update(learn_is_paid=True)
						b_logo_users.update(logo_is_paid=True)
						b_link_users.update(link_is_paid=True)
						b_plug_users.update(plug_is_paid=True)
						b_post_users.update(post_is_paid=True)
						b_share_users.update(share_is_paid=True)
						b_embed_users.update(embed_is_paid=True)
						b_internel_embed_users.update(embed_is_paid=True)
						b_view_users.update(view_is_paid=True)
						b_home_view_users.update(view_is_paid=True)
						b_monthly_logo.update(is_paid=True)
						b_monthly_skigit.update(is_paid=True)
						b_donate_skigit.update(donate_is_paid=True)
						b_qr_code.update(qrcode_is_paid=True)

						response_data['is_success'] = True
						response_data['message'] = '$%s amount is received.' % Decimal(result.transaction.amount)
						response_data['transaction_id'] = result.transaction.id
						response_data['transaction_date'] = datetime.datetime.now().strftime("%b %d, %Y")
				else:
						response_data['is_success'] = False
						response_data['amount'] = amount
						for error in result.errors.deep_errors:
								response_data['message'] = error.message
								response_data['code'] = error.code
								response_data['attribute'] = error.attribute
		else:
				response_data['is_success'] = False
				response_data['message'] = 'Payment method does not exist!'
		return response_data

def get_invoices(user_id, data):
		user = get_object_or_None(User, id=user_id)
		year = data.get('year', 0)
		month = int(data.get('month', 0))
		month_list = ['January', 'February', 'March', 'April', 'May', 'Jun', 'July', 'August', 'September',
									'October', 'November', 'December']
		business_invoices_list = []
		year_list = range(user.date_joined.year, datetime.datetime.now().year + 1)

		if not year:
				year = datetime.datetime.now().year
		month = datetime.datetime.now().month
		if not int(year) == datetime.datetime.now().year:
				if int(month) == 1:
						year = int(year) - 1
				month = 12
		date = datetime.date(int(year), month, 1)

		if user.profile.payment_method == '0':
				inv = Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False).first()
				card_type = inv.type
				card_detail = inv.email
				card_img = inv.c_image_url
		elif user.profile.payment_method == '1':
				inv = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=False).first()
				card_type = inv.type
				card_detail = str('%06d*****%04d') % (int(inv.first_6), int(inv.last_4))
				card_img = inv.c_image_url
		else:
				card_type, card_detail, card_img = None

		if user.date_joined.year == year:
				start_range = user.date_joined.month
		else:
				start_range = 1
		for i in range(start_range, month + 1 if not int(year) == datetime.datetime.now().year else month + 1):
				b_learn_more_users, b_logo_users, b_link_users, b_plug_users, b_post_users, b_share_users,\
				b_embed_users, total_amount, payment_recived, b_internel_embed_users, b_view_users, b_home_view_users,\
				b_monthly_logo, b_monthly_skigit, b_qr_code = invoice_total_amount(
						user,
						# date=date,
						month=i,
						year=year)
						
				payment_info = {
						'current_month': datetime.datetime.now().month,
						'year': year,
						'month': month_list[i - 1],
						'month_num': i,
						'transaction_id': payment_recived.first().transaction_id if payment_recived.exists() else None,
						'transaction_date': payment_recived.first().created_date.strftime(
								"%b %d, %Y") if payment_recived.exists() else None,
						'total_amount': total_amount,
						'learn_more_detail': b_learn_more_users.first(),
						'logo_detail': b_logo_users.first(),
						'link_detail': b_link_users.first(),
						'plug_detail': b_plug_users.first(),
						'post_detail': b_post_users.first(),
						'share_detail': b_share_users.first(),
						'embed_detail': b_embed_users.first(),
						'internel_embed_detail': b_internel_embed_users.first(),
						'view_detail': b_view_users.first(),
						'home_view_detail': b_home_view_users.first(),
						'b_monthly_logo': b_monthly_logo.first(),
						'monthly_logo_fee': config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY,
						'b_monthly_skigit': b_monthly_skigit.first(),
						'qr_code_detail':  b_qr_code.first(),
						'card_type': card_type,
						'card_detail': card_detail,
						'card_img': card_img,
						'inv': inv
				}

				business_invoices_list.append(payment_info)
		business_invoices_list = sorted(business_invoices_list, key=itemgetter('month_num'), reverse=True)
		return business_invoices_list

def create_paypal_payment_customer(user_id, data, request=None):
		'''
		Manages paypal account creation
		:param user_id:
		:param data:
		:return:
		'''
		response_data = {'is_success': False, 'message': 'Invalid Card details'}
		user = get_object_or_None(User, id=user_id)

		if not Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False).exists():
				if Profile.objects.filter(user=user).exists():
						profile_obj = Profile.objects.get(user=user)
						if profile_obj.company_title:
								company = profile_obj.company_title
						else:
								company = None
				nonce_from_the_client = data.get('nonce', None)
				card_type = data.get('type', None)
				result = braintree.Customer.create({
						'first_name': user.first_name,
						'last_name': user.last_name,
						'company': company,
						'payment_method_nonce': nonce_from_the_client,
				})
				if result.is_success:
						invoice_obj = None
						customer_transaction = find_pay_pal_customer(request, result.customer.payment_methods[0].token)

						inv = Invoice.objects.create(user=user, customer_id=customer_transaction.customer_id,
																				 type=card_type, email=customer_transaction.email,
																				 billing_agreement_id=customer_transaction.billing_agreement_id,
																				 c_image_url=customer_transaction.image_url,
																				 payment_method_token=customer_transaction.token)
						if inv:
								invoice_obj = Invoice.objects.get(user=user, type='PayPalAccount', is_deleted=False)
								response_data['is_success'] = True
								response_data['message'] = 'PayPal information Successfully saved on Braintree Vault.'
								response_data['invoice'] = {'email': invoice_obj.email, 'type': invoice_obj.type,
																						'card_image': invoice_obj.c_image_url}
						else:
								response_data['is_success'] = False
								response_data['message'] = 'PayPal information saved on Braintree Vault. Data missing.'
				else:
						response_data['is_success'] = False
						for error in result.errors.for_object("customer"):
								response_data['message'] = error.message
								response_data['error_code'] = error.code
								response_data['error_attribute'] = error.attribute
		else:
				invoice_obj = Invoice.objects.get(user=user, type='PayPalAccount', is_deleted=False)
				response_data['is_success'] = True
				response_data['message'] = 'This Customer Already Exists With PayPalAccount Details'
				response_data['invoice'] = {'email': invoice_obj.email, 'type': invoice_obj.type,
																		'card_image': invoice_obj.c_image_url}
		return response_data

def create_payment_customer(user_id, data, request=None):
		user = get_object_or_None(User, id=user_id)
		response_data = {'is_success': False, 'message': 'Invalid Card details'}

		exists_invoice = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=False).exists()
		deleted_invoice = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=True).exists()

		if not exists_invoice:
				nonce_from_the_client = data.get('nonce', None)
				cardholder_name = data.get('name_on_card', None)
				card_type = data.get('type', None)

				if Profile.objects.filter(user=user).exists():
						profile_obj = Profile.objects.get(user=user)
						if profile_obj.biller_address1 and profile_obj.biller_address2:
								address = '%s %s' % (str(profile_obj.biller_address1), str(profile_obj.biller_address2))
						elif profile_obj.biller_address1:
								address = '%s' % str(profile_obj.biller_address1)
						elif profile_obj.biller_address1:
								address = '%s' % str(profile_obj.biller_address2)
						else:
								address = 'Address Not mention by user %s' % user.username

						if not deleted_invoice:
								result = braintree.Customer.create({
										'first_name': user.first_name,
										'last_name': user.last_name,
										'company': profile_obj.company_title,
										'email': user.email,
										'credit_card': {
												'cardholder_name': cardholder_name,
												"payment_method_nonce": nonce_from_the_client,
												'options': {
														'verify_card': True,
												},
												'billing_address': {
														'first_name': user.first_name,
														'last_name': user.last_name,
														'company': profile_obj.company_title,
														'street_address': address,
														'locality': profile_obj.city,
														'region': profile_obj.state,
														'postal_code': profile_obj.zip_code
												},
										},
								})
						else:
								inv = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=True).order_by('-created_date').first()
								result = braintree.Customer.update(inv.customer_id, {
										'first_name': user.first_name,
										'last_name': user.last_name,
										'company': profile_obj.company_title,
										'email': user.email,
										'credit_card': {
												'cardholder_name': cardholder_name,
												"payment_method_nonce": nonce_from_the_client,
												'options': {
														'verify_card': True,
														'make_default': True,
												},
												'billing_address': {
														'first_name': user.first_name,
														'last_name': user.last_name,
														'company': profile_obj.company_title,
														'street_address': address,
														'locality': profile_obj.city,
														'region': profile_obj.state,
														'postal_code': profile_obj.zip_code
												},
										},
								})
				else:
						if not deleted_invoice:
								result = braintree.Customer.create({
										'first_name': user.first_name,
										'last_name': user.last_name,
										'email': user.email,
										'credit_card': {
												'cardholder_name': cardholder_name,
												"payment_method_nonce": nonce_from_the_client,
												'options': {
														'verify_card': True,
														'make_default': True,
												},
												'billing_address': {
														'first_name': user.first_name,
														'last_name': user.last_name,
												},
										},
								})
						else:
								inv = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=True).order_by('-created_date').first()
								result = braintree.Customer.update(inv.customer_id, {
										'first_name': user.first_name,
										'last_name': user.last_name,
										'email': user.email,
										'credit_card': {
												'cardholder_name': cardholder_name,
												"payment_method_nonce": nonce_from_the_client,
												'options': {
														'verify_card': True,
												},
												'billing_address': {
														'first_name': user.first_name,
														'last_name': user.last_name,
												},
										},
								})
				if result.is_success:
						invoice_obj = None
						customer_transaction = find_customer(request, result.customer.payment_methods[0].token)
						last4 = '%4d' % int(customer_transaction.last_4)
						inv = Invoice.objects.create(user=user, customer_id=customer_transaction.customer_id,
																				 last_4=last4, first_6=customer_transaction.bin,
																				 credit_card_type=customer_transaction.card_type, type=card_type,
																				 c_image_url=customer_transaction.image_url,
																				 cardholder_name=customer_transaction.cardholder_name,
																				 customer_location=customer_transaction.customer_location,
																				 issuing_bank=customer_transaction.issuing_bank,
																				 country_of_issuance=customer_transaction.country_of_issuance,
																				 card_status=customer_transaction.verifications[0]['status'],
																				 payment_method_token=customer_transaction.token,
																				 merchant_account_id=customer_transaction.verifications[0][
																						 'merchant_account_id'],
																				 cvv_response_code=customer_transaction.verifications[0][
																						 'cvv_response_code'],
																				 currency_iso_code=customer_transaction.verifications[0][
																						 'currency_iso_code'],
																				 processor_response_code=customer_transaction.verifications[0][
																						 'processor_response_code'],
																				 unique_number_identifier=customer_transaction.unique_number_identifier,
																				 debit=customer_transaction.debit)
						if inv:
								invoice_obj = Invoice.objects.get(user=user, type='CreditCard', is_deleted=False)
								response_data['is_success'] = True
								response_data['message'] = 'Card Information Successfully saved on Braintree Vault.'
								response_data['invoice'] = {'issuing_bank': customer_transaction.issuing_bank,
																						'card': str('%06d****%04d') % (
																								int(customer_transaction.bin), int(last4)),
																						'credit_card_type': customer_transaction.card_type,
																						'card_status': customer_transaction.verifications[0]['status'],
																						'card_image': customer_transaction.image_url,
																						'cardholder_name': customer_transaction.cardholder_name}
						else:
								response_data['is_success'] = False
								response_data['message'] = 'Card saved on Braintree Vault. but Retrieving data failed.'
				else:
						response_data['is_success'] = False
						for error in result.errors.for_object("customer").for_object("credit_card"):
								response_data['message'] = error.message
								response_data['error_code'] = error.code
								response_data['error_attribute'] = error.attribute
		elif deleted_invoice:
				invoice

		else:
				invoice_obj = Invoice.objects.get(user=user, type='CreditCard', is_deleted=False)
				response_data['is_success'] = True
				response_data['message'] = 'This Customer Already Exists With Card Details'
				response_data['invoice'] = {'issuing_bank': invoice_obj.issuing_bank,
																		'card': str('%06d****%04d') % (
																				int(invoice_obj.first_6), int(invoice_obj.last_4)),
																		'credit_card_type': invoice_obj.credit_card_type,
																		'card_status': invoice_obj.card_status,
																		'card_image': invoice_obj.c_image_url,
																		'cardholder_name': invoice_obj.cardholder_name}
		return response_data

def delete_payment_type(user_id, data):
		response_data = {'is_success': False, 'message': 'Error into removing card/paypal details.'}
		account_type = data.get('type', None)
		user = get_object_or_None(User, id=user_id)

		try:
				inv = Invoice.objects.filter(user=user, type=account_type, is_deleted=False)[0]
				logger.info("Delete Pay Inv %s", inv)
				inv.is_deleted=True
				inv.save()
				# remove the payment method from Braintree
				result = braintree.PaymentMethod.delete(inv.payment_method_token)
				logger.info("Delete Pay result %s", result)
				response_data['is_success'] = True
				if inv:
						response_data['message'] = '%s details removed successful' % (account_type)
				else:
						response_data['message'] = '%s details are not there.' % (account_type)
		except Exception as e:
				logger.error("Delete payment Api: %s", e)
				response_data['is_success'] = False
				response_data['message'] = 'Exception in Payment Account Removal time. Failed to remove.'
		return response_data

class CreatePaymentCustomerAPIView(views.APIView):
		permission_classes = (CustomIsAuthenticated,)

		def post(self, request):
				result = {}
				response_data = {'message': 'Invalid Card details',
												 'success': 'error'}
				try:
						data = request.data.copy()
						user_id = request.user.id if request.auth else 0
						data.update(user_id=user_id)
						method_type = data.get('type', '')

						if method_type == 'PayPalAccount':
								response_data = create_paypal_payment_customer(user_id, data)
						elif method_type == 'CreditCard':
								response_data = create_payment_customer(user_id, data)
						status = 'success' if response_data['is_success'] else 'error'
						message = response_data['message'] if response_data['message'] else ''

						result.update(status=status,
													message=message,
													data=response_data['invoice'] if 'invoice' in response_data else {})
				except Exception as exc:
						logger.error("Serializer: Create Payment customer APIView:", exc)
						result.update(status='error',
													message='Invalid Card details')
				return Response(result)


class PaymentCustomerDetailAPIView(views.APIView):
		permission_classes = (CustomIsAuthenticated,)

		def get(self, request):
				result = {'message': ''}

				try:
						data = request.query_params
						method_type = data.get('type', '')
						user = request.user if request.auth else None
						response_data = get_payment_customer_token(user, method_type)
						result.update(status='success',
													data=response_data)
						if not response_data:
								result.update(message="There is no payment detail!")
				except Exception as exc:
						logger.error("Serializer: Payment Customer Detail APIView:", exc)
						result.update(status='error',
													message='Error into getting payment customer details.')
				return Response(result)


class DeletePaymentTypeAPIView(views.APIView):
		permission_classes = (CustomIsAuthenticated,)

		def post(self, request):
				result = {}
				response_data = {'message': 'Error into removing card/paypal details.',
												 'success': 'error'}
				try:
						data = request.data.copy()
						logger.info("Delete API data: %s", data)
						user_id = request.user.id if request.auth else 0
						data.update(user_id=user_id)
						logger.info("Delete API adter update data: %s", data)

						response_data = delete_payment_type(user_id, data)
						logger.info("Delete API response data: %s", response_data)
						status = 'success' if response_data['is_success'] else 'error'
						message = response_data['message'] if response_data['message'] else ''
						result.update(status=status,
													message=message)
				except Exception as exc:
						logger.error("Serializer: Delete Payment Type APIView:", exc)
						result.update(status='error',
													message='Error into removing card/paypal details.')
				return Response(result)


class InvoiceListAPIView(generics.ListAPIView):
		serializer_class = InvoiceDetailSerializer
		permission_classes = (CustomIsAuthenticated,)

		def get_queryset(self):
				data = self.request.query_params.copy()
				user_id = request.user.id if request.auth else 0
				data.update(user_id=user_id)
				user = get_object_or_None(User, id=user_id)

				if user.profile.payment_method == '0':
						queryset = Invoice.objects.filter(user=user, type='PayPalAccount', is_deleted=False).first()
				elif user.profile.payment_method == '1':
						queryset = Invoice.objects.filter(user=user, type='CreditCard', is_deleted=False).first()
				else:
						queryset = []
				return queryset

		def get(self, request):
				result = {}
				response_data = {'message': 'Invoices are not loading. Please try again.',
												 'success': 'error'}
				try:
						data = request.query_params.copy()
						user_id = request.user.id if request.auth else 0
						data.update(user_id=user_id)

						invoices = get_invoices(user_id, data)
						page = self.paginate_queryset(invoices)
						if page is not None:
								serializer = self.get_serializer(page, many=True)
								paginated_result = self.get_paginated_response(serializer.data)
								data = paginated_result.data
						else:
								serializer = self.get_serializer(vid, many=True)
								data = serializer.data
						result.update(status='success',
													message='',
													data=data)
				except Exception as exc:
						logger.error("Serializer: Invoices List APIView:", exc)
						result.update(status='error',
													message='Invoices are not loading. Please try again.')
				return Response(result)


class InvoicePayAPIView(views.APIView):
		permission_classes = (CustomIsAuthenticated,)

		def post(self, request):
				result = {}
				response_data = {'message': 'Error into Paying bill, please contact administrator.',
												 'success': 'error'}
				try:
						data = request.data.copy()
						user_id = request.user.id if request.auth else 0
						data.update(user_id=user_id)

						response_data = manage_pay_invoice(user_id, data)
						status = 'success' if response_data['is_success'] else 'error'
						message = response_data['message'] if response_data['message'] else ''
						response_data.pop('is_success')
						response_data.pop('message')
						result.update(status=status,
													message=message,
													data=response_data)
				except Exception as exc:
						logger.error("Serializer: Invoice Payment APIView:", exc)
						result.update(status='error',
													message='Error into Paying bill, please contact administrator.')
				return Response(result)


class SkigitViewFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				  'message': ''}
		data = request.data.copy()
		skigit_id = data.get('skigit_id', None)
		view_page = data.get('view_page', 0)
		try:
			response_data = skigit_view_fees(skigit_id, view_page, request)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit view error", exc)
			response_data.update(status="error",\
				message='Error: View Invoice! Try again later or contact Administrator')

		response_data.pop('is_success', None)
		return Response(response_data)


class SkigitWebLinkFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				  'message': ''}
		data = request.data.copy()
		web_user = data.get('link_user', None)
		logger.error("web_user id is {}".format(web_user))
		web_url = data.get('weblink', None)
		logger.error("web_user id is {}".format(web_url))
		try:
			response_data = weblink_fees(web_user, web_url, request)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit weblink error", exc)
			response_data.update(status="error",\
				message='Error in to Weblink Invoice! Try again Later or Contact to Administrator.')

		response_data.pop('is_success', None)
		return Response(response_data)


class SkigitBusinessLogoFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				  'message': ''}
		data = request.data.copy()
		logo = data.get('logo_id', None)
		try:
			response_data = business_logo_fees(logo, request)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit business logo fee error", exc)
			response_data.update(status="error",\
				message='Business Logo Error. Submit this bug to the Skigit Administrator. Thank you!')

		response_data.pop('is_success', None)
		return Response(response_data)

class SkigitQRCodeFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				'message': ''}
		data = request.data.copy()
		b_user = data.get('user', None)
		try:
			response_data = qr_code_fees(b_user)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit qr code fee error", exc)
			response_data.update(status="error",\
				message='QR Code  Error. Submit this bug to the Skigit Administrator. Thank you!')

		response_data.pop('is_success', None)
		return Response(response_data)

class SkigitSocialPostFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				  'message': ''}
		data = request.data.copy()
		ski_user = data.get('skigit_user', None)
		ski_id = data.get('skigit_id', None)
		social_type = data.get('social_type', None)
		try:
			response_data = business_post_fees(ski_user, ski_id, social_type, request)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit social post fee error", exc)
			response_data.update(status="error",\
				message='Error in to Social post Invoice! Try again Later or Contact to Administrator.')

		response_data.pop('is_success', None)
		return Response(response_data)


class SkigitEmbedFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				  'message': ''}
		data = request.data.copy()
		ski_id = data.get('skigit_id', None)
		try:
			response_data = business_embed_fees(ski_id, request)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit embed fee error", exc)
			response_data.update(status="error",\
				message='Error in to Embed Invoice! Try again Later or Contact to Administrator.')

		response_data.pop('is_success', None)
		return Response(response_data)


class SkigitLearnMoreFeeAPIView(views.APIView):
	permission_classes = (CustomIsAuthenticated,)

	def post(self, request):
		response_data = {'is_success': '', "status":"",
				  'message': ''}
		data = request.data.copy()
		login_id = data.get('login_id', None)
		skigit_id = data.get('skigit_id', None)
		try:
			response_data = learn_more_fees(login_id, skigit_id, request)
			response_data.update(status="success")
		except Exception as exc:
			logger.error("Skigit learn more fee error", exc)
			response_data.update(status="error",\
				message='Error in to Learn More Invoice! Try again Later or Contact to Administrator.')

		response_data.pop('is_success', None)
		return Response(response_data)

def updateMonthlyLogoInvoice(user, logo):
	current_month = datetime.datetime.now().date().month
	current_year = datetime.datetime.now().date().year

	existing_record = MonthlyLogoInvoice.objects.filter(user=user, billing_month__month=current_month,
													billing_month__year=current_year).order_by('-id')
	if existing_record.exists():
		last_record = existing_record.first()
		last_record.total_count = 1
		last_record.total_amount = config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY
		last_record.save()
	else:
		total_count = 1
		total_amount = config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY
		MonthlyLogoInvoice.objects.create(user=user,
														billing_month=datetime.datetime.now().date(),
														logo_amount=config.FEE_BUSINESS_SKIGIT_LOGO_MONTHLY,
														total_logo_count=total_count,
														logo_total_amount=total_amount
														)

def updateMonthlySkigitInvoice(video_detail, action):
	if is_user_business(video_detail.skigit_id.user):
		current_month = datetime.datetime.now().date().month
		current_year = datetime.datetime.now().date().year

		# check if skigit invoice exist agaist that user for current month
		if not MonthlySkigitInvoice.objects.filter(user=video_detail.skigit_id.user, skigit=video_detail, billing_month__month=current_month,
														billing_month__year=current_year).exists():

			existing_record = MonthlySkigitInvoice.objects.filter(user=video_detail.skigit_id.user, billing_month__month=current_month,
															billing_month__year=current_year
															).order_by('-id')

			query = False
			if existing_record.exists():
				query = True
				last_record = existing_record.first()
				total_count = last_record.total_skigit_count + Decimal(1)
				total_amount = last_record.skigit_total_amount + Decimal(config.FEE_BUSINESS_SKIGIT_MONTHLY_MAINTENANCE)

			else:
				# if record not exist then check in logo table
				exisiting_skigits = VideoDetail.objects.select_related('skigit_id').filter(
					skigit_id__user=video_detail.skigit_id.user, status=1, is_active=True)
				if exisiting_skigits:
					query = True
					total_count = exisiting_skigits.count()
					total_amount = Decimal(config.FEE_BUSINESS_SKIGIT_MONTHLY_MAINTENANCE) * total_count
				elif action == 'approved':
					query = True
					total_count = 1
					total_amount = config.FEE_BUSINESS_SKIGIT_MONTHLY_MAINTENANCE

			if query:
				MonthlySkigitInvoice.objects.create(user=video_detail.skigit_id.user,
																skigit=video_detail,
																billing_month=datetime.datetime.now().date(),
																skigit_amount=config.FEE_BUSINESS_SKIGIT_MONTHLY_MAINTENANCE,
																total_skigit_count=total_count,
																skigit_total_amount=total_amount
																)


def business_donate_invoice(business_user, video_id, incentive_amount):
	"""
	Business donate Invoice when selecting logo and donate.
	"""

	response_data = {'is_success': False,
					 'message': 'Error in to Donate Invoice! Try again Later or Contact to Administrator.'}

	business_user = User.objects.get(pk=business_user)
	video_obj = VideoDetail.objects.get(id=video_id)
	current_date = datetime.datetime.now().date()
	try:
		donate_invoice = DonateInvoice.objects.create(user=business_user,
													  video=video_obj,
													  billing_month=current_date,
													  donate_amount=incentive_amount)
		current_month_donate_invoices = DonateInvoice.objects.filter(user=business_user,
									 billing_month=current_date,
									 donate_is_paid=False)
		total_amount_obj = current_month_donate_invoices.aggregate(total_amount=Sum('donate_amount'))
		response_data['is_success'] = True
		response_data['message'] = "Donation Current Month {0}'s Count {1} and Due Amount is:{2}".format(
								    donate_invoice.billing_month.month, current_month_donate_invoices.count(),
									total_amount_obj['total_amount'])

	except Exception as exc:
		response_data['is_success'] = True
		response_data['message'] = 'Skigit is property of Current user/ General user -' \
								   ' Charges are not applicable.'

	return response_data


def update_donate_unpaid_invoices(user):
	"""

	:param user:
	:return:

	Updates the donate value if the incentive value changes in the profile update!
	"""

	profile = user.profile
	DonateInvoice.objects.filter(user=user, donate_is_paid=False).update(donate_amount=profile.incetive_val)
	return ()

@login_required(login_url='/login')
def userPaymentSetupStatus(request):
		"""
				Check User payment setup. Is it successfully setup or not
		"""
		response_data = {'paymentSetupExist': False,
										 'message': 'Get User Payment Info Successfully'}

		try :
			if is_user_business(request.user) and not Invoice.objects.filter(user=request.user, type='CreditCard',
																	is_deleted=False).exists() and not \
							Invoice.objects.filter(user=request.user, type='PayPalAccount', is_deleted=False).exists():
				response_data['paymentSetupExist'] = False
			else: 
				response_data['paymentSetupExist'] = True
		except 	Exception as exc:
				response_data = {'paymentSetupExist': False,'message': 'Error in Geting user payment info'}

		return json_response(response_data)


def qr_code_fees(b_user_id):
	response_data = {'is_success': False,
					'message': 'Error in to QR Code Invoice! Try again Later or Contact to Administrator.'}

	profile = Profile.objects.get(user=b_user_id)
	if is_user_business(profile.user):
			current_month = datetime.datetime.now().date().month
			current_year = datetime.datetime.now().date().year
			b_user = User.objects.get(id=b_user_id)
			qrCodeInvoice = QRCodeInvoice.objects.filter(user=b_user,billing_month__month=current_month,billing_month__year=current_year)
			if qrCodeInvoice:
				last_record = qrCodeInvoice.first()
				last_record.qrcode_count += Decimal(1)
				last_record.qrcode_amount += Decimal(config.QR_CODE_SCAN)
				last_record.save()
				response_data['is_success'] = True
				response_data['message'] = 'QR Code Invoice updated successfully'
			else:
				QRCodeInvoice.objects.create(user=b_user, 
															qrcode_count=1,
															billing_month=datetime.datetime.now().date(),
															qrcode_amount=config.QR_CODE_SCAN)

				response_data['is_success'] = True
				response_data['message'] = 'QR Code Invoice updated successfully'
				
	return response_data