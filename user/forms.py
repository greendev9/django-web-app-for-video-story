from datetime import date
import re

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from datetime import datetime
from django import forms

from email_validator import validate_email, EmailNotValidError, EmailUndeliverableError

from user.models import ProfileImg, Profile

from dateutil.relativedelta import relativedelta

class RegistrationForm(forms.Form):
    username = forms.RegexField(regex=r'^\w+$', widget=forms.TextInput(
        attrs=dict(required=True, max_length=30)
    ), label=_("Username"), error_messages={
        'invalid': _("This value must contain only letters, numbers and underscores.")})
    email = forms.EmailField(widget=forms.TextInput(
        attrs=dict(required=True, max_length=30)
    ), label=_("Email address"))
    password1 = forms.CharField(widget=forms.PasswordInput(
        attrs=dict(required=True, max_length=30, render_value=False)
    ), label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs=dict(required=True, max_length=30, render_value=False)
    ), label=_("Password (again)"))

    def clean_username(self):
        try:
            User.objects.get(
                username__iexact=self.cleaned_data['username']
            )
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_("The username already exists. "
                                      "Please try another one."))

    def clean_email(self):
        try:
            email = self.cleaned_data['email']
            validate_email(email)
            User.objects.get(
                email__iexact=email
            )
        except (EmailUndeliverableError, EmailNotValidError):
            raise forms.ValidationError(_("This email is not valid one."))
        except User.DoesNotExist:
            return self.cleaned_data['email']
        raise forms.ValidationError(_("This email is already in use. Please try another."))

    def clean(self):
        password_validator = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,16}$'

        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields "
                                              "did not match."))
            elif not re.match(password_validator, self.cleaned_data['password1']):
                raise forms.ValidationError(_("Your password must contain minimum of 8 characters with at least one upper case character"))
        return self.cleaned_data


class UserForm(forms.ModelForm):
    username = forms.CharField(max_length=100,
                               disabled=True,
                               required=False)
    email = forms.EmailField(disabled=True,label='Email',
                             required=False)

    class Meta:
        model = User
        widgets = {
            'first_name': forms.TextInput(
                attrs={'placeholder': 'First Name', 'required': 'True'}
            ),
            'last_name': forms.TextInput(
                attrs={'placeholder': 'Last Name', 'required': 'True'}
            ),
            'password': forms.TextInput(attrs={
                'required': 'True', 'max_length': '30', 'render_value': 'False'
            }),
        }
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *ar, **kw):
        super(UserForm, self).__init__(*ar, **kw)
        instance = kw['instance'] if kw.get('instance', '') else ''
        if not instance.email:
            self.fields['email'].disabled = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(u'User with this Email address already exists.')
        return email


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['gender'].choices = self.fields['gender'].choices[1:]

    max_birth_date = (datetime.now() -  relativedelta(years = 13)).date()
    birthdate = forms.DateInput(
                attrs={'placeholder': 'Date Of Birth', 'required': 'True','class': 'form-control','type': 'date','max': max_birth_date}
            ),

    def clean_birthdate(self):
        # validate age. need to be more than 13 years old
        birthdate = self.cleaned_data['birthdate']
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if age < 13:
            raise forms.ValidationError(u'You need to be at least 13 years of age to be a member of Skigit')
        else:
            return birthdate

    def clean_phone_num(self):
        # remove non numerical string
        phone_num = self.cleaned_data['phone_num']
        phone_num = ''.join(e for e in phone_num if e.isdigit())
        return phone_num
        
    class Meta:
        model = Profile
        max_birth_date = (datetime.now() -  relativedelta(years = 13)).date()
        widgets = {
            'profile_img': forms.FileInput(
                attrs={'placeholder': 'Profile Picture'}
            ),
            'birthdate': forms.DateInput(
                attrs={'placeholder': 'Date Of Birth', 'required': 'True','class': 'form-control','type': 'date','max': max_birth_date}
            ),
            'zip_code': forms.TextInput(
                attrs={'placeholder': 'zip_code', 'required': 'True'}
            ),
            'gender': forms.RadioSelect(
                attrs={'placeholder': 'Gender', 'required': 'True'},
            ),
            'language': forms.Select(
                attrs={'placeholder': 'Language', 'required': 'True'}
            ),
            'country': forms.Select(
                attrs={'placeholder': 'country', 'required': 'True','onchange' : "onSelectCountry(this.value);"}
            ),
            'state': forms.TextInput(
                attrs={'placeholder': 'state', 'required': 'True'}
            ),
            'city': forms.TextInput(
                attrs={'placeholder': 'city', 'required': 'True'}
            ),
            'about_me': forms.Textarea(
                attrs={'placeholder': 'About Me', 'rows': '4', 'required': 'True'}
            ),
            'phone_num': forms.TextInput(
                attrs={'placeholder': 'Contact Phone', 'required': 'True'}
            ),

        }
        fields = ('profile_img', 'gender', 'birthdate', 'about_me', 'language', 'country', 'state', 'city', 'zip_code', 'phone_num',
                  'search_profile_security')


class SignupForm(forms.Form):
    pass

    def signup(self, request, user):
        user.is_active = False
        role = request.session.get('user_type')
        g = Group.objects.get(name=settings.GENERAL_USER)
        user.groups.add(g)
        user.save()


class BusinessUserProfileForm(forms.ModelForm):
    max_birth_date = (datetime.now() -  relativedelta(years = 13)).date()
    birthdate = forms.DateInput(
                attrs={'placeholder': 'Date Of Birth', 'required': 'True','class': 'form-control','type': 'date','max': max_birth_date}
            ),
    contact_email = forms.EmailField(required=True, error_messages={'required': "This field required"},
                                     label='Contact email')
    payment_email = forms.EmailField(required=False, error_messages={'required': "This field required"},
                                     label='Payment email')

    def __init__(self, *args, **kwargs):
        super(BusinessUserProfileForm, self).__init__(*args, **kwargs)
        self.fields['gender'].choices = self.fields['gender'].choices[1:]
        self.fields['incentive'].choices = self.fields['incentive'].choices[1:]

    def clean_birthdate(self):
        # validate age. need to be more than 13 years old
        birthdate = self.cleaned_data['birthdate']
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if age < 13:
            raise forms.ValidationError(u'You need to be at least 13 years of age to be a member of Skigit')
        else:
            return birthdate

    def clean_contact_phone(self):
        # remove non numerical string
        contact_phone = self.cleaned_data['contact_phone']
        contact_phone = ''.join(e for e in contact_phone if e.isdigit())
        return contact_phone
          
    class Meta:
        model = Profile
        max_birth_date = (datetime.now() -  relativedelta(years = 13)).date()
        widgets = {
            'profile_img': forms.FileInput(
                attrs={'placeholder': 'Profile Picture'}
            ),
            'company_title': forms.TextInput(
                attrs={'placeholder': 'Company Title', 'required': 'True'}
            ),
            'zip_code': forms.TextInput(
                attrs={'placeholder': 'zip_code', 'required': 'True'}
            ),
            'gender': forms.RadioSelect(
                attrs={'placeholder': 'Gender', 'required': 'True'},
            ),
            'birthdate': forms.DateInput(
                attrs={'placeholder': 'Date Of Birth', 'required': 'True','class': 'form-control','type': 'date','max': max_birth_date}
            ),
            'incentive': forms.RadioSelect(
                attrs={'placeholder': 'Incentive', 'required': 'True'},
            ),
            'language': forms.Select(
                attrs={'placeholder': 'Language', 'required': 'True'}
            ),
            'country': forms.Select(
                attrs={'placeholder': 'country', 'required': 'True','onchange' : "onSelectCountry(this.value);"}
            ),
            'city': forms.TextInput(
                attrs={'placeholder': 'city', 'required': 'True'}
            ),
            'coupan_image': forms.FileInput(
                attrs={'placeholder': 'Coupan Image'}
            ),
            'contact_name': forms.TextInput(
                attrs={'placeholder': 'Contact Name', 'required': 'True'}
            ),
            'contact_phone': forms.TextInput(
                attrs={'placeholder': 'Contact Phone', 'required': 'True'}
            ),
            'incetive_val': forms.TextInput(
                attrs={'placeholder': 'Incentive value', "autocomplete": "off"}
            ),
            'payment_user_name': forms.TextInput(
                attrs={'placeholder': 'Payment Name', 'required': 'True'}
            ),
            'business_type':
                forms.Select(
                    attrs={'placeholder': 'business_type', 'required': 'True','onchange' : "onSelectBusinessType(this.value);"}
                ),
            'custom_business_type':
                forms.TextInput(
                    attrs={'placeholder': '', 'required': 'False'}
                ),
            'payment_method': forms.RadioSelect(
                attrs={'placeholder': 'Payment Method', 'required': 'True'},
            ),
            'ein': forms.TextInput(attrs={'placeholder': 'Enterprise ID', 'required': 'True'}),

            'business_website': forms.TextInput(
                attrs={'placeholder': 'Business Website.'}
            ),
            'biller_name': forms.TextInput(
                attrs={'onkeydown': 'return /[a-z A-Z\-]/i.test(event.key)', 'required': 'True'}
            ),
        }

        fields = ('profile_img', 'company_title', 'gender', 'birthdate', 'about_me', 'language', 'country',
                  'state', 'city', 'zip_code', 'search_profile_security', 'incentive', 'skigit_incentive',
                  'redemoption_instrucations', 'coupan_code', 'incetive_val', 'contact_name', 'contact_email',
                  'contact_phone', 'biller_name', 'payment_method', 'biller_address1', 'biller_address2',
                  'payment_email', 'payment_user_name', 'business_type','custom_business_type', 'ein', 'business_website')


class ProfileNotificationForm(forms.ModelForm):
    class Meta:
        model = Profile
        widgets = {

            'like_notify': forms.CheckboxInput(),
            'follow_un_follow_notify': forms.CheckboxInput(),
            'friends_request_notify': forms.CheckboxInput(),
            'friends_accept_notify': forms.CheckboxInput(),
            'plug_notify': forms.CheckboxInput(),
            'un_plug_notify': forms.CheckboxInput(),
            'skigit_notify': forms.CheckboxInput(),
            'share_notify': forms.CheckboxInput(),

        }

        fields = ('like_notify', 'follow_un_follow_notify', 'friends_request_notify', 'friends_accept_notify',
                  'plug_notify', 'un_plug_notify', 'skigit_notify', 'share_notify')


class ProfileImgForm(forms.ModelForm):
    class Meta:
        model = ProfileImg
        widgets = {
            'profile_img': forms.FileInput(
                attrs={'placeholder': 'Cover Images', 'multiple': 'multiple'}
            ),
        }
        fields = ('profile_img',)


class UserApiForm(UserForm):
    """
    Add required attributes!
    """

    def __init__(self, *ar, **kw):
        super(UserApiForm, self).__init__(*ar, **kw)
        instance = kw['instance'] if kw.get('instance', '') else ''
        required_fields = ('username', 'email', 'first_name', 'last_name')
        for i in required_fields:
            if i == 'email':
                if instance.email:
                    self.fields[i].required = False
                else:
                    self.fields[i].disabled = False
            else:
                self.fields[i].required = True
        if not instance.email:
            self.fields['email'].required = True

    def save(self, commit=True):
        user = super(UserApiForm, self).save(commit=False)
        if commit:
            if self.instance.email is not None and self.instance.email != '':
                user.email = self.instance.email
            user.save()
        return user

class BusinessUserProfileApiForm(BusinessUserProfileForm):

    """
    Add required fields for business profile
    """
    birthdate_day = forms.IntegerField(label='Birth day')
    birthdate_month = forms.IntegerField(label='Birth month')
    birthdate_year = forms.IntegerField(label='Birth year')

    def __init__(self, *ar, **kw):
        super(BusinessUserProfileApiForm, self).__init__(*ar, **kw)
        required_fields = ('company_title', 'gender', 'birthdate', 'about_me', 'language', 'country',
                           'state', 'city', 'zip_code', 'search_profile_security', 'incentive', 'contact_name',
                           'contact_email', 'contact_phone', 'biller_name', 'payment_method', 'biller_address1',
                           'payment_email', 'payment_user_name', 'business_type',
                           'birthdate_day', 'birthdate_month', 'birthdate_year')
        for i in required_fields:
            self.fields[i].required = True
        self.fields['payment_user_name'].label = 'Payment Name'


class ProfileApiForm(ProfileForm):
    """
    Add required fields for general profile
    """
    birthdate_day = forms.IntegerField(label='Birth day')
    birthdate_month = forms.IntegerField(label='Birth month')
    birthdate_year = forms.IntegerField(label='Birth year')

    def __init__(self, *ar, **kw):
        super(ProfileApiForm, self).__init__(*ar, **kw)
        required_fields = ('gender', 'birthdate', 'about_me', 'language', 'country', 'state', 'city', 'zip_code', 'phone_num',
                           'search_profile_security', 'birthdate_day', 'birthdate_month', 'birthdate_year')

        for i in required_fields:
            self.fields[i].required = True


class CustomPasswordResetForm(PasswordResetForm):
    error_messages = {
        'password_mismatch': ("The two password fields didn't match."),
    }
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control required', 'required': ''}),
                             error_messages={'required': 'Email address is required',
                                             'invalid': 'Please enter a valid email address'})

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            validate_email(email)
            User.objects.get(
                email__iexact=email
            )
        except (EmailUndeliverableError, EmailNotValidError):
            raise forms.ValidationError(_("This email address is not valid one."))
        except User.DoesNotExist:
            raise forms.ValidationError(_("This email address is not found."))
        return email

class TwoFactorAuthForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TwoFactorAuthForm, self).__init__(*args, **kwargs)
        self.fields['two_fa_by_email'].initial = self.user.profile.two_fa_by_email
        self.fields['two_fa_by_app'].initial = self.user.profile.two_fa_by_app

    class Meta:
        model = Profile
        fields = ('two_fa_by_email', 'two_fa_by_app')


