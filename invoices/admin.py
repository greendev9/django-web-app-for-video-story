# Register your models here.

from django.contrib import admin

# from daterange_filter.filter import DateRangeFilter
from constance import config

from invoices.models import *
from django.utils.html import format_html

class VisitorAdmin(admin.ModelAdmin):
    """ Business Logo Admin
    """
    list_display = ['logo_charge', 'link_charge', 'plug_charge', 'post_charge', 'share_charge', 'embed_charge']

    def has_add_permission(self, request):
        """ Override Add Permission (Display False)
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """ Override Add Permission (Display False)
        """
        return False

admin.site.register(VisitCharges, VisitorAdmin)


class BusinessLogoAdmin(admin.ModelAdmin):
    """ Business Logo Admin
    """
    exclude = ['business_logo']
    # readonly_fields = ['get_logo', 'logo_user', 'user', 'get_month_year', 'logo_count', 'logo_total_amount',
    #                    'total_logo_count', 'user_total_due']
    list_display = ['get_logo', 'logo_user', 'user', 'logo_count', 'total_logo_count', 'logo_total_amount',
                    'user_total_due', 'get_month_year', 'logo_is_paid', ]
#    list_filter = ['created_date', 'updated_date', 'billing_month', ('billing_month', DateRangeFilter)]
    search_fields = ['logo_count', 'logo_user__first_name', 'logo_user__username', 'logo_user__last_name',
                     'billing_month', ]

    ordering = ('-billing_month', 'logo_user', '-created_date',)
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    # def get_year(self, obj):
    #     """
    #         Billing Year
    #     """
    #     if obj.billing_month:
    #         return obj.billing_month.strftime("%Y")
    # get_year.allow_tags = True
    # get_year.short_description = 'Billing Year'
    # get_year.admin_order_field = 'billing_month'

    def get_logo(self, obj):
        """
            Business Logo
        """
        if obj.business_logo:
            img = format_html('<img src="%s" width="35px" height="35px" />' % obj.business_logo.logo.url)
            return img
    get_logo.allow_tags = True
    get_logo.short_description = 'Business Logo'
    get_logo.admin_order_field = 'business_logo'

    def get_charges(self, obj):
        """
            Billing Charges
        """
        return config.FEE_LOGO_CLICK
    get_charges.allow_tags = True
    get_charges.short_description = 'Business Logo Charge'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False

admin.site.register(BusinessLogoInvoice, BusinessLogoAdmin)


class WebLinkAdmin(admin.ModelAdmin):
    """ Business Web Link Admin
    """

    list_display = ['web_link_user', 'user', 'get_charges', 'link_count', 'link_due_amount', 'link_total_count',
                    'link_total_due', 'get_month_year', 'link_is_paid']
#    list_filter = ['created_date', 'updated_date', 'billing_month', ('billing_month', DateRangeFilter)]
    search_fields = ['link_count', 'user__first_name', 'user__username', 'user__last_name',
                     'billing_month']

    ordering = ('-billing_month', '-created_date',)
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    # def get_year(self, obj):
    #     """
    #         Billing Year
    #     """
    #     if obj.billing_month:
    #         return obj.billing_month.strftime("%Y")
    # get_year.allow_tags = True
    # get_year.short_description = 'Billing Year'
    # get_year.admin_order_field = 'billing_month'

    def get_charges(self, obj):
        """
            Billing Charges
        """
        #visitor = VisitCharges.objects.all()[0]
        return config.FEE_WEBSITE_LINKS_CLICK
    get_charges.allow_tags = True
    get_charges.short_description = 'Web Link Charge'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False


class LearnMoreAdmin(admin.ModelAdmin):
    """ Business Learn more Admin
    """

    list_display = ['user', 'get_charges', 'learn_count', 'learn_due_amount', 'learn_total_count',
                    'learn_total_due', 'get_month_year', 'learn_is_paid']
#    list_filter = ['created_date', 'updated_date', 'billing_month', ('billing_month', DateRangeFilter)]
    search_fields = ['learn_count', 'user__first_name', 'user__username', 'user__last_name',
                     'billing_month']

    ordering = ('-billing_month', '-created_date',)
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    # def get_year(self, obj):
    #     """
    #         Billing Year
    #     """
    #     if obj.billing_month:
    #         return obj.billing_month.strftime("%Y")
    # get_year.allow_tags = True
    # get_year.short_description = 'Billing Year'
    # get_year.admin_order_field = 'billing_month'

    def get_charges(self, obj):
        """
            Billing Charges
        """
        return config.FEE_LEARN_MORE
    get_charges.allow_tags = True
    get_charges.short_description = 'Learn more Charge'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False


class SocialPostAdmin(admin.ModelAdmin):
    """
        Business Social Post Admin
    """

    list_display = ['logo_user', 'user', 'social_network_type', 'get_charges', 'post_ski', 'get_ski_user', 'post_count',
                    'skigit_post_amount', 'post_total_count', 'post_total_amount', 'get_month_year', 'post_is_paid']
#    list_filter = ['created_date', 'updated_date', 'social_network_type', 'billing_month',
#                   ('billing_month', DateRangeFilter), ]
    search_fields = ['post_count', 'logo_user__first_name', 'logo_user__username', 'social_network_type',
                     'skigit_user__last_name', 'billing_month', 'post_ski', ]

    ordering = ('social_network_type', '-created_date',)
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    # def get_year(self, obj):
    #     """
    #         Billing Year
    #     """
    #     if obj.billing_month:
    #         return obj.billing_month.strftime("%Y")
    # get_year.allow_tags = True
    # get_year.short_description = 'Billing Year'
    # get_year.admin_order_field = 'billing_month'

    def get_charges(self, obj):
        """
            Billing Charges
        """
        return config.FEE_SOCIAL_NETWORK_POST
    get_charges.allow_tags = True
    get_charges.short_description = 'Post Charge'

    def get_ski_user(self, obj):
        """
            Skigit User
        """
        if obj.post_ski:
            return '%s' % obj.post_ski.skigit_id.user.username
    get_ski_user.allow_tags = True
    get_ski_user.short_description = 'Skigit Uploader'
    get_ski_user.admin_order_field = 'post_ski__skigit_id__user__username'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False

admin.site.register(PostInvoice, SocialPostAdmin)


class PluginAdmin(admin.ModelAdmin):
    """
        Business PlugIn Admin
    """

    list_display = ['skigit_user', 'user', 'get_charges', 'plugin_ski', 'primary_ski', 'plugin_count',
                    'current_plugin_amount', 'plugin_total_count', 'plugin_total_amount', 'get_month_year',
                    'plug_is_paid', ]
#    list_filter = ['created_date', 'updated_date', 'billing_month', ('billing_month', DateRangeFilter), ]
    search_fields = ['plugin_count', 'skigit_user__first_name', 'skigit_user__username', 'skigit_user__last_name',
                     'billing_month', ]

    ordering = ('-skigit_user', '-created_date')
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    # def get_year(self, obj):
    #     """
    #         Billing Year
    #     """
    #     if obj.billing_month:
    #         return obj.billing_month.strftime("%Y")
    # get_year.allow_tags = True
    # get_year.short_description = 'Billing Year'
    # get_year.admin_order_field = 'billing_month'

    def get_charges(self, obj):
        """
            Billing Charges
        """
        return config.FEE_SKIGIT_PLUGIN
    get_charges.allow_tags = True
    get_charges.short_description = 'PlugIn Charge'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False

admin.site.register(PluginInvoice, PluginAdmin)


class ShareAdmin(admin.ModelAdmin):
    """
        Business Share Admin
    """

    list_display = ['skigit_user', 'user', 'get_charges', 'share_ski', 'share_count', 'skigit_share_amount',
                    'total_share_count', 'share_total_amount', 'get_month_year', 'share_is_paid', ]
#    list_filter = ['created_date', 'updated_date', 'billing_month', ('billing_month', DateRangeFilter), ]
#    search_fields = ['plugin_count', 'skigit_user__first_name', 'skigit_user__username', 'skigit_user__last_name',
#                     'billing_month', ]

    ordering = ('-skigit_user', '-created_date')
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    # def get_year(self, obj):
    #     """
    #         Billing Year
    #     """
    #     if obj.billing_month:
    #         return obj.billing_month.strftime("%Y")
    # get_year.allow_tags = True
    # get_year.short_description = 'Billing Year'
    # get_year.admin_order_field = 'billing_month'

    def get_charges(self, obj):
        """
            Billing Charges
        """
        return config.FEE_SKIGIT_SHARE
    get_charges.allow_tags = True
    get_charges.short_description = 'Share Charge'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False

admin.site.register(ShareInvoice, ShareAdmin)

class MonthlyLogoMaintenanceAdmin(admin.ModelAdmin):
    """
        Business Monthly Logo Admin
    """
    list_display = ['user', 'logo_amount', 'total_logo_count', 'logo_total_amount','get_month_year', 'is_paid', ]

    ordering = ('-user', '-created_date')
    list_per_page = 25



    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    def get_queryset(self, request):
        from django.db.models.functions import ExtractMonth
        qs = super(MonthlyLogoMaintenanceAdmin, self).get_queryset(request)
        return qs.distinct('user_id')

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False

admin.site.register(MonthlyLogoInvoice, MonthlyLogoMaintenanceAdmin)


class MonthlySkigitMaintenanceAdmin(admin.ModelAdmin):
    """
        Business Share Admin
    """

    list_display = ['user', 'skigit_amount', 'total_skigit_count', 'skigit_total_amount', 'get_month_year', 'is_paid',  ]

    ordering = ('-user', '-created_date')
    list_per_page = 25

    def get_queryset(self, request):
        qs = super(MonthlySkigitMaintenanceAdmin, self).get_queryset(request)
        return qs.distinct('user_id')

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'


    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False

admin.site.register(MonthlySkigitInvoice, MonthlySkigitMaintenanceAdmin)


class EmbedAdmin(admin.ModelAdmin):
    """
        Business Share Admin
    """

    list_display = ['user', 'skigit_user', 'get_charges', 'embed_ski', 'embed_count', 'skigit_embed_amount',
                    'embed_total_amount', 'embed_total_count', 'get_month_year', 'embed_is_paid', ]
#    list_filter = ['created_date', 'updated_date', 'billing_month', ('billing_month', DateRangeFilter), ]
    search_fields = ['plugin_count', 'skigit_user__first_name', 'skigit_user__username', 'skigit_user__last_name',
                     'billing_month', ]

    ordering = ('-skigit_user', '-created_date')
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    # def get_year(self, obj):
    #     """
    #         Billing Year
    #     """
    #     if obj.billing_month:
    #         return obj.billing_month.strftime("%Y")
    # get_year.allow_tags = True
    # get_year.short_description = 'Billing Year'
    # get_year.admin_order_field = 'billing_month'

    def get_charges(self, obj):
        """
            Billing Charges
        """
        return config.FEE_SKIGIT_EMBED_MY_SITE
    get_charges.allow_tags = True
    get_charges.short_description = 'Embed Charge'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False


class DonateInvoiceAdmin(admin.ModelAdmin):
    """
        Business Donate Admin
    """

    list_display = ['user', 'get_month_year', 'donate_is_paid']
    search_fields = ['user__first_name', 'user__username', 'user__last_name', 'billing_month']

    ordering = ('-user', '-created_date')
    list_per_page = 25

    def get_month_year(self, obj):
        """
            Billing Month
        """
        if obj.billing_month:
            return '%s %s' % (str(obj.billing_month.strftime("%B")), str(obj.billing_month.strftime("%Y")))
    get_month_year.allow_tags = True
    get_month_year.short_description = 'Billing Month/Year'
    get_month_year.admin_order_field = 'billing_month'

    def has_add_permission(self, request):
        """
            Override Add Permission (Display False)
        """
        return False


admin.site.register(EmbedInvoice, EmbedAdmin)
admin.site.register(Invoice)
admin.site.register(InvoiceBilling)
admin.site.register(WebLinkInvoice, WebLinkAdmin)
admin.site.register(LearnMoreInvoice, LearnMoreAdmin)
admin.site.register(DonateInvoice, DonateInvoiceAdmin)
