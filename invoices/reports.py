import pytz
import csv
import os
from calendar import monthrange
from datetime import datetime, timedelta
from operator import itemgetter
import calendar
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, render
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from invoices.models import BusinessLogoInvoice, WebLinkInvoice, PluginInvoice, \
    PostInvoice, ShareInvoice, EmbedInvoice, VisitCharges, LearnMoreInvoice, InternalEmbedInvoice

from invoices.views import invoice_total_amount

from skigit.models import Favorite, Like, VideoDetail

from django.contrib import admin


# Pagination
class CustomAdminPaginationList(object):
    can_show_all = True
    multi_page = True
    get_query_string = ChangeList.__dict__['get_query_string']

    def __init__(self, request, page_num, paginator):
        self.show_all = 'all' in request.GET
        self.page_num = page_num
        self.paginator = paginator
        self.result_count = paginator.count
        self.params = dict(request.GET.items())


class MyTemplateView(TemplateView):

    template_name = 'invoices/report_invoices.html'

    def get(self, request, *args, **kwargs):
        export_csv = self.request.GET.get('export_csv', None)
        export_txt = self.request.GET.get('export_txt', None)
        if export_csv:
            return self._export_csv()
        elif export_txt:
          return self._export_txt()
        else:
            return super(MyTemplateView, self).get(request, *args, **kwargs)

    def users(self):
        users = User.objects.filter(groups__name=settings.BUSINESS_USER)
        user_list = []
        for user in users:
            udict = {'id': user.id, 'name': user.username}
            user_list.append(udict)
        sorted_user_list = sorted(user_list, key = lambda i: (i['name'].lower()))
        return sorted_user_list

    def years(self):
      year = datetime.today().year
      year_list = range(2015,year + 1)
      return year_list

    def months(self):
      months_choices = []
      # now = datetime.now()
      for i in range(1, 13):
        months_choices.append(calendar.month_name[i])
      months = dict(enumerate((name for name in months_choices if name), start=1))
      return months
    
    def results(self):
        sel_year = self.request.GET.get('year', None)
        sel_month = self.request.GET.get('month', None)
        user_id = self.request.GET.get('buser', None)

        sel_year = int(sel_year) if sel_year else sel_year
        sel_month = int(sel_month) if sel_month else sel_month
        user_id = int(user_id) if user_id else user_id
        
        data = []
        busers = VideoDetail.objects.exclude(business_user_id__isnull=True).filter(is_active=True)
        if user_id:
            busers = busers.filter(business_user_id = int(user_id))
        if sel_year:
            busers = busers.filter(business_user__date_joined__year = sel_year)
        if sel_month:
            busers = busers.filter(business_user__date_joined__month = sel_month)
            
        for buser in busers:
            ulist = {}
            ulist['id'] = buser.business_user.id
            ulist['business_name'] = buser.business_user.profile.company_title
            ulist['m_start_date'] = buser.business_user.date_joined.strftime('%m/%d/%Y')
            ulist['m_end_date'] = ''
            ulist['m_months_running'] = self._membership_months(buser.business_user)
            if buser.business_logo_id:
                ulist['business_logo'] = 'Yes'
                ulist['logo_upload_date'] = buser.business_logo.created_date.strftime('%m/%d/%Y')
            else:
                ulist['business_logo'] = 'No'
                ulist['logo_upload_date'] = '-'
            ulist['logo_delete_date'] = '-'
            ulist['skigit_creator'] = buser.skigit_id.user.username
            ulist['skigit_uploaded'] = buser.title
            ulist['skigit_id'] = buser.id
            ulist['skigit_upload_date'] = buser.created_date.strftime('%m/%d/%Y')
            ulist['skigit_upload_delete'] = ''
            ulist['logo_click'] = self._logo_clicks(buser.business_user, buser.business_logo)
            ulist['learn_more'] = self._learn_more(buser.skigit_id.user, buser)
            ulist['shares'] = self._shares(buser.business_user, buser)
            ulist['plugins'] = self._plugins(buser.business_user, buser)
            ulist['likes'] = self._likes(buser)
            ulist['views'] = buser.view_count
            ulist['favorites'] = Favorite.objects.filter(skigit=buser.skigit_id, is_active=True).count()
            ulist['embedded_internal'] = InternalEmbedInvoice.objects.filter(user=buser.skigit_id.user, embed_ski=buser).count()
            ulist['embedded_external'] = EmbedInvoice.objects.filter(user=buser.skigit_id.user, embed_ski=buser).count()
            ulist['sperk_value'] = buser.business_user.profile.incetive_val
            ulist['sperk_donate_receive'] = self._donate_receive(buser)
            if buser.donate_skigit:
                ulist['charity'] = buser.donate_skigit.ngo_name
            else:
                ulist['charity'] = '-'
            data.append(ulist)
        data = sorted(data, key = lambda i: (i['business_name'].lower()))
        result = {'data': data,
                  'users': self.users(),
                  'years': self.years(),
                  'months': self.months(),
                  'sel_year': sel_year,
                  'sel_month': sel_month,
                  'sel_user': user_id
                  }
        return result

    def _membership_months(self, user):
        d1 = user.date_joined
        d2 = datetime.today().replace(tzinfo=pytz.utc)
        delta = 0
        while True:
            mdays = monthrange(d1.year, d1.month)[1]
            d1 += timedelta(days=mdays)
            if d1 <= d2:
                delta += 1
            else:
                break
        return delta

    def _export_csv(self):
      result = self.results()
      if os.path.exists("/tmp/export_csv.csv"):
          os.remove("/tmp/export_csv.csv")
      response = HttpResponse(content_type='text/csv')
      response['Content-Disposition'] = 'attachment; filename=invoices.csv'

      writer = csv.DictWriter(response, fieldnames=result['data'][0].keys())
      writer.writeheader()
      
      for item in result['data']:
          writer.writerow(item)
      return response
    
    def _export_txt(self):
      result = self.results()
      if os.path.exists("/tmp/export_txt.txt"):
          os.remove("/tmp/export_txt.txt")
      response = HttpResponse(content_type='text/csv')
      response['Content-Disposition'] = 'attachment; filename=invoices.txt'

      writer = csv.DictWriter(response, fieldnames=result['data'][0].keys())
      writer.writeheader()
      
      for item in result['data']:
          writer.writerow(item)
      return response

    def _logo_clicks(self, user, logo):
        blogo = BusinessLogoInvoice.objects.filter(logo_user=user, business_logo=logo)
        if blogo:
            return blogo[0].logo_count
        else:
            return '-'

    def _shares(self, user, skigit):
        items = ShareInvoice.objects.filter(user=user, share_ski=skigit)
        if items:
            return items[0].share_count
        else:
            return '-'

    def _plugins(self, user, skigit):
        items = PluginInvoice.objects.filter(skigit_user=user, plugin_ski=skigit)
        if items:
            return items[0].plugin_count
        else:
            return '-'

    def _likes(self, skigit):
        return Like.objects.filter(skigit=skigit.skigit_id).count()

    def _donate_receive(self, skigit):
        if skigit.receive_donate_sperk == 1:
            return 'D'
        if skigit.receive_donate_sperk == 2:
            return 'R'
        else:
            return '-'

    def _learn_more(self, user, skigit):
        items = LearnMoreInvoice.objects.filter(user=user, learn_ski=skigit)
        if items:
            return items[0].learn_count
        else:
            return '-'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.results())
        context.update(admin.site.each_context(self.request))

        return context


class UnPaidCustomerView(TemplateView):
    template_name = 'invoices/unpaid_invoice.html'
    #user_list = []
    per_page = 10

    def results(self):
        user_id = self.request.GET.get('buser', None)
        page = int(self.request.GET.get('p', 0))
        user_list = []
        data = []
        cur_date = datetime.now()
        sel_year = self.request.GET.get('year', None)
        sel_month = self.request.GET.get('month', None)
        # sel_user = self.request.GET.get('buser', None)
        month_list = ['January', 'February', 'March', 'April', 'May', 'Jun', 'July', 'August', 'September',
                      'October', 'November', 'December']

        if sel_month:
            sel_month = int(sel_month)
            month_values = [month_list[sel_month - 1]]
        else:
            month_values = month_list

        sel_year = int(sel_year) if sel_year else sel_year
        # if not year:
        #    year = datetime.now().year
        # month = datetime.now().month

        # date_value = datetime(int(year), invoice_month, 1)
        busers = VideoDetail.objects.exclude(business_user_id__isnull=True).filter(is_active=True).\
                                             values_list('business_user',
                                                         flat=True).distinct()
        if user_id:
            busers = busers.filter(business_user_id=int(user_id))
        busers = User.objects.filter(id__in=busers)
        year_range = range(cur_date.year - 2, cur_date.year + 1)

        for buser in busers:
            is_un_paid = False
            """if buser.date_joined.year == year:
                start_range = buser.date_joined.month
            else:
                start_range = 1"""
            for year in reversed(year_range):
                if (sel_year and year == sel_year) or not sel_year:
                    for i, month_name in enumerate(reversed(month_values), 1):
                        month_value = month_list.index(month_name.strip()) + 1
                        b_learn_more_users, b_logo_users, b_link_users, b_plug_users, b_post_users, b_share_users, \
                        b_embed_users, total_amount, payment_recived, b_internel_embed_users, b_view_users, b_home_view_users,\
                        b_skigit_logo_monthly, b_skigit_monthly_maintenance, b_donate_skigit,b_qr_code = invoice_total_amount(
                            buser,
                            month=month_value,
                            year=year
                        )
                        if (b_learn_more_users.exists() or b_logo_users.exists() or b_link_users.exists() or b_plug_users.exists() or
                            b_post_users.exists() or b_share_users.exists() or b_embed_users.exists() or b_internel_embed_users.exists() \
                            or b_view_users.exists() or b_home_view_users.exists() or b_skigit_logo_monthly.exists() or b_skigit_monthly_maintenance.exists() or \
                            b_donate_skigit.exists()
                        ) and not payment_recived.exists():
                            invoice_detail = {'id': buser.id,
                                              'business_name': buser.profile.company_title,
                                              'user_name': buser.username,
                                              'year': year,
                                              'month': month_name,
                                              # 'month_num': i,
                                              'total_amount': total_amount}
                            data.append(invoice_detail)
                            is_un_paid = True
            if is_un_paid:
                udict = {'id': buser.id, 'name': buser.username}
                user_list.append(udict)
        """if data:
            data = sorted(data,
                          key=itemgetter('month_num'),
                          reverse=True)"""

        paginator = Paginator(data, self.per_page)

        try:
            data = paginator.page(page + 1)
        except EmptyPage:
            data = paginator.page(paginator.num_pages)

        cl = CustomAdminPaginationList(self.request, page, paginator)

        result = {'data': data,
                  'cl': cl,
                  'users': user_list,
                  'month_list': month_list,
                  'year_list': reversed(year_range),
                  'sel_year': sel_year,
                  'sel_month': sel_month}
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # unpaid_invoices, users = self.results()
        # users = {'users': self.users()}
        # context.update({'cl': self.results()})
        context.update(self.results())
        # context.update(user_list)
        context.update(admin.site.each_context(self.request))
        return context
