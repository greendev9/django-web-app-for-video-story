from django.contrib import admin
from mailpost.models import EmailTemplate, EmailHeader, EmailFooter, EmailHost
from django_summernote.admin import SummernoteModelAdmin

class EmailTemplateAdmin(SummernoteModelAdmin):
    """ Add control of EmailTemplate module in Django Admin """
    list_display = ['template_name', 'template_key', 'subject',
                    'from_email', 'created_date', 'modified_date']
    summernote_fields = ('html_template',)
    save_as = True

admin.site.register(EmailTemplate, EmailTemplateAdmin)

class EmailHeaderAdmin(admin.ModelAdmin):
    """ Add control of EmailHeader module in Django Admin """
    list_display = ['template_key', 'created_date', 'modified_date']
    save_as = True

admin.site.register(EmailHeader, EmailHeaderAdmin)

class EmailFooterAdmin(admin.ModelAdmin):
    """ Add control of EmailFooter module in Django Admin """
    list_display = ['template_key', 'created_date', 'modified_date']
    save_as = True

admin.site.register(EmailFooter, EmailFooterAdmin)

class EmailHostAdmin(admin.ModelAdmin):
    """ Add control of EmailHost module in Django Admin """
    list_display = ['email','host_name', 'created_date', 'modified_date']
    save_as = True

admin.site.register(EmailHost, EmailHostAdmin)
