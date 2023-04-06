from django import forms
from django.forms import widgets
from django.contrib.auth.models import User
from django.conf import settings
from .fields import BusinessProfileNameField
from skigit.models import CopyRightInfringement, UploadedVideo, UploadedVideoLink, VideoDetail

from user.models import PROFILE_DEACTIVATE_REASON_CHOICES

class HorizontalRadioRenderer(widgets.RadioSelect):
    template_name = 'widgets/horizontal_select.html'

    # def render(self):
    #     return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


class YoutubeUploadForm(forms.Form):
    token = forms.CharField()
    title = forms.CharField(required=True)
    file = forms.FileField(required=True)




class SkigitUploadForm(forms.ModelForm):
    made_by = BusinessProfileNameField(queryset=User.objects.filter(groups__name=settings.BUSINESS_USER,
                                                                  profile__payment_method__isnull=False,
                                                                  profile__payment_email__isnull=False,
                                                                  profile__business_verified=True,
                                                                  invoice_user__type__in=['PayPalAccount', 'CreditCard'],
                                                                  invoice_user__is_deleted=False
                                                                    ).\
                                     order_by('profile__company_title')[:10])

    def __init__(self, *args, **kwargs):
        super(SkigitUploadForm, self).__init__(*args, **kwargs)
        self.fields['made_by'].empty_label = ""
        self.fields['category'].empty_label = "Select a Skigit Category"
        self.fields['donate_skigit'].empty_label = "Select your favourite cause"
        self.fields['subject_category'].empty_label = "Select a Subject Category"

    class Meta:
        model = VideoDetail
        CHOICES = (('1', 'On',), ('2', 'Off',))

        widgets = {
            'receive_donate_sperk': forms.RadioSelect(
                attrs={'placeholder': 'Sperk', 'required': 'True', 'class': 'form-control'}
            ),

            'add_logo': forms.RadioSelect(
                attrs={'name': 'add_logo', 'required': 'True'}, choices=CHOICES
            ),
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter your Skigit Title', 'required': 'True', 'class': 'form-control',
                'unique': 'True', 'maxlength': '40'
            }),
            'category': forms.Select(attrs={
                'placeholder': 'Select a skigit category', 'required': 'True', 'class': 'form-control'
            }),
            'subject_category': forms.Select(attrs={
                'placeholder': 'Select a Subject category', 'required': 'True', 'class': 'form-control'
            }),
            'made_by': forms.Select(
                attrs={'placeholder': 'Select a made by', 'required': 'True', 'class': 'form-control',
                       'help_text': 'Select maker'}
            ),
            'donate_skigit': forms.Select(
                attrs={'placeholder': 'Select your favourite cause', 'class': 'form-control',
                       'help_text': 'Select your favourite cause'}
            ),
            'why_rocks': forms.Textarea(attrs={'required': True, 'class': 'form-control','rows':4}),
            'made_by_option': forms.TextInput(attrs={'required': False, 'class': 'form-control'}),
            'bought_at': forms.TextInput(attrs={'required': True, 'class': 'form-control'}),
        }
        exclude = ('skigit_id', 'business_user', 'status', 'is_share',
                   'share_skigit', 'inappropriate_skigit', 'is_plugged',
                   'is_sperk', 'plugged_skigit', 'incentive', 'is_active')


class YoutubeDirectUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedVideo
        fields = ['file_on_server']


class YoutubeLinkUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedVideoLink
        widgets = {
            'video_link': forms.TextInput(attrs={'class': 'form-control'})
        }
        fields = ('video_link',)


class CopyrightInfringementForm(forms.ModelForm):

    signature = forms.CharField(max_length=200, required=True)

    def __init__(self, *args, **kwargs):
        super(CopyrightInfringementForm, self).__init__(*args, **kwargs)
        self.fields['submitter_request'].choices = (self.fields['submitter_request']).choices[0:]

    class Meta:
        model = CopyRightInfringement
        fields = ['urls', 'skigit_id', 'submitter_request', 'address', 'city', 'state', 'zip_code', 'country',
                  'phone', 'email', 'full_name', 'signature']
        widgets = {
            'skigit_id': forms.TextInput(
                attrs={'placeholder': '',
                       'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off', 'name': 'skigit_id',
                       'class': 'form-control', 'required': 'True', 'readonly': True}),
            'full_name': forms.TextInput(
                attrs={'placeholder': 'Your Full Name', 'name': 'full_name', 'autocomplete': 'off',
                       'autocorrect': 'off',
                       'autocapitalize': 'off', 'class': 'form-control', 'required': 'True'}),
            'address': forms.TextInput(
                attrs={'placeholder': 'Street Address', 'name': 'address', 'class': 'form-control', 'required': 'True',
                       'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'city': forms.TextInput(
                attrs={'placeholder': 'City', 'name': 'city', 'class': 'form-control', 'required': 'True',
                       'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'state': forms.TextInput(
                attrs={'placeholder': 'State', 'name': 'state', 'class': 'form-control', 'required': 'True',
                       'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'country': forms.Select(
                attrs={'class': 'form-control', 'required': 'True', 'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'zip_code': forms.TextInput(
                attrs={'placeholder': 'Zip/Postal Code', 'class': 'form-control', 'required': 'True',
                       'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'phone': forms.TextInput(
                attrs={'placeholder': 'phone', 'class': 'form-control', 'required': 'True', 'autocomplete': 'off',
                       'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'signature': forms.TextInput(
                attrs={'placeholder': 'Electronic signature', 'class': 'form-control', 'required': 'True',
                       'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'email': forms.EmailInput(
                attrs={'placeholder': 'email', 'class': 'form-control', 'required': 'True', 'autocomplete': 'off',
                       'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'urls': forms.URLInput(
                attrs={'placeholder': 'URL', 'class': 'form-control', 'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'}),
            'submitter_request': forms.RadioSelect(
                attrs={'placeholder': 'remove_all', 'required': 'True', 'autocomplete': 'off', 'autocorrect': 'off',
                       'autocapitalize': 'off'})
        }


class DeleteProfileForm(forms.Form):
    delete_account_confirm = forms.BooleanField(widget=forms.CheckboxInput(attrs={'id': 'delete-account',
                                                                     'value': '1'}))
    delete_reason = forms.CharField(max_length=20, widget=forms.Select(choices=PROFILE_DEACTIVATE_REASON_CHOICES,
                                                                       attrs={'required': 'required',
                                                                              'class': 'form-control'}))
    delete_reason_other = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)

    def clean_delete_reason_other(self):
        data = self.cleaned_data
        if data['delete_reason'] == 'other':
            if data['delete_reason_other']:
                return data['delete_reason_other']
            else:
                raise forms.ValidationError('This field is required!')
        return data['delete_reason_other']