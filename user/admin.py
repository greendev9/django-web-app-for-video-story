from django.contrib import admin

from .models import BusinessLogo, BusinessDoc, ExtraProfileImage

admin.site.register(BusinessLogo)
admin.site.register(BusinessDoc)
admin.site.register(ExtraProfileImage)