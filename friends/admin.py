from django.contrib import admin

from friends.models import Friend, FriendInvitation, Notification, \
    InviteMessage, WallPoster, PosterBusinessLogo, Brochure, BrochureBLogo
from django import forms
from tinymce.widgets import TinyMCE

admin.site.register(FriendInvitation)
admin.site.register(Friend)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'user', 'msg_type', 'is_read']


class InviteMessageForm(forms.ModelForm):
    invite_message = forms.CharField(
        widget=TinyMCE(
            attrs={'cols': 100, 'rows': 30, 'font-size': 'large'}
        )
    )

    class Meta:
        model = InviteMessage
        exclude = []


class InviteMessageAdmin(admin.ModelAdmin):
    form = InviteMessageForm

    class Admin:
        js = ('js/tiny_mce/tiny_mce.js',
              'js/tiny_mce/textareas.js',
              )
admin.site.register(InviteMessage, InviteMessageAdmin)


class WallPosterAdmin(admin.ModelAdmin):
    # form = WallPosterForm

    class Admin:
        js = ('js/tiny_mce/tiny_mce.js',
              'js/tiny_mce/textareas.js',
              )
admin.site.register(WallPoster, WallPosterAdmin)

admin.site.register(PosterBusinessLogo)

admin.site.register(Brochure)
admin.site.register(BrochureBLogo)
admin.site.register(Notification, NotificationAdmin)