import random
import hashlib
from datetime import datetime, timedelta
import re

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from rest_framework import serializers
from django_countries import countries

from sorl.thumbnail import get_thumbnail
from email_validator import validate_email, EmailNotValidError, EmailUndeliverableError

from user.models import (User, Profile, BusinessLogo, ExtraProfileImage, ProfileUrl,
                         DEVICE_TYPE_CHOICES)
from mailpost.models import EmailTemplate
from social.models import Follow

from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import PasswordField

from core.utils import (get_all_logged_in_users, get_profile_status,
                        get_object_or_None, is_user_business, is_user_general)


def api_request_images(image_file, **kwargs):
    # get host url like https://www.skigit.com
    host = ''.join(settings.HOST)[:-1]

    try:
        thumbnail_image = get_thumbnail(image_file,
                                        "{0}x{1}".format(image_file.width,
                                                         image_file.height),
                                        **kwargs)
    except Exception as e:
        thumbnail_image = str(image_file)
    # concat host with image url
    res = "{0}{1}".format(settings.MEDIA_HOST_URL, thumbnail_image)
    return res


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'created_at', 'updated_at',
                  'first_name', 'last_name', 'password',
                  'confirm_password',)
        read_only_fields = ('created_at', 'updated_at',)

        def create(self, validated_data):
            return User.objects.create(**validated_data)

        def update(self, instance, validated_data):
            instance.username = validated_data.get(
                'username', instance.username)

            instance.save()

            password = validated_data.get('password', None)
            confirm_password = validated_data.get('confirm_password', None)

            if password and confirm_password and password == confirm_password:
                instance.set_password(password)
                instance.save()

            update_session_auth_hash(self.context.get('request'), instance)

            return instance


class RegisterSerializer(serializers.Serializer):
    ACCOUNT_TYPE_CHOICES = [
        ['general', 'General'],
        ['business', 'Business']
    ]

    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField()
    accType = serializers.ChoiceField(choices=ACCOUNT_TYPE_CHOICES,
                                      required=True)
    deviceToken = serializers.CharField(max_length=500,
                                        required=False)
    deviceType = serializers.ChoiceField(choices=DEVICE_TYPE_CHOICES,
                                         default='web')
    password1 = serializers.CharField(write_only=True,
                                      style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True,
                                      style={'input_type': 'password'})

    def validate_username(self, value):
        data = self.get_initial()
        if value:
            try:
                User.objects.get(
                    username__iexact=value
                )
            except User.DoesNotExist:
                return value
            if 'deviceType' in data and data['deviceType'] in ['ios', 'android']:
                error = _("This email is already in use. Please try another.")
            else:
                error = _("The username already exists. "
                          "Please try another one.")
            raise serializers.ValidationError(error)
        else:
            return value

    def validate_email(self, value):
        try:
            validate_email(value)
            User.objects.get(
                email__iexact=value
            )
        except (EmailUndeliverableError, EmailNotValidError):
            raise serializers.ValidationError(
                _("This email is not valid one."))
        except User.DoesNotExist:
            return value
        raise serializers.ValidationError(
            _("This email is already in use. Please try another."))

    def validate(self, data):
        password_validator = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,16}$'

        if 'password1' in data and 'password2' in data:
            if data['password1'] != data['password2']:
                raise serializers.ValidationError(_("The two password fields "
                                                    "did not match."))
            elif not re.match(password_validator, data['password1']):
                raise serializers.ValidationError(_("Your password must contain minimum "
                                                    "of 8 characters with at least one upper case character"))
        if not data.get('username', None):
            raise serializers.ValidationError(_("Email is required!"))

        return data

    def create(self, validated_data):
        username = validated_data.get('username')

        group_name = settings.BUSINESS_USER if validated_data.get(
            'accType') == 'business' else settings.GENERAL_USER

        user = User.objects.create_user(
            username=username,
            password=validated_data['password1'],
            email=validated_data['email']
        )
        user.is_active = False
        user.save()
        g = Group.objects.get(name=group_name)
        g.user_set.add(user)

        email = validated_data['email']
        random_string = str(random.random()).encode('utf8')
        salt = hashlib.sha1(random_string).hexdigest()[:5]
        salted = (salt + email).encode('utf8')
        activation_key = hashlib.sha1(salted).hexdigest()
        key_expires = datetime.today() + timedelta(1)
        if validated_data['deviceType'] != 'ios' or validated_data['deviceType'] != 'android':
            validated_data['deviceType'] = 'android'
        else:
            pass
        # Save The Hash to user Profile
        new_profile = Profile(user=user, activation_key=activation_key,
                              key_expires=key_expires,
                              device_type=validated_data['deviceType'])

        new_profile.save()

        confirm_path = "/register/confirm/%s" % activation_key
        confirm = validated_data.get(
            'request').build_absolute_uri(confirm_path)

        template_key = "new_registration_confirm_business" if group_name == settings.BUSINESS_USER else "new_registration_confirm_general"

        EmailTemplate.send(
            template_key=template_key,
            emails=email,
            context={"confirm_link": confirm})
        return user


class ProfileUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30, required=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    # password = serializers.CharField(write_only=True,
    #                                 style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class ProfileSerializer(serializers.ModelSerializer):
    user = ProfileUserSerializer(many=False)
    profile_img = serializers.SerializerMethodField()
    gender = serializers.ChoiceField(
        choices=Profile.GENDER_CHOICES, required=True)
    birthdate = serializers.DateField(required=True)
    about_me = serializers.CharField(max_length=300, required=True)
    language = serializers.ChoiceField(
        choices=Profile.LANGUAGE_CHOICES, required=True)
    country = serializers.SerializerMethodField()
    state = serializers.CharField(max_length=10, required=True)
    city = serializers.CharField(max_length=50, required=True)
    zip_code = serializers.CharField(max_length=6, required=True)
    phone_num = serializers.CharField(max_length=12, required=True)
    search_profile_security = serializers.BooleanField()

    class Meta:
        model = Profile
        fields = ('user', 'profile_img', 'gender', 'birthdate', 'about_me', 'language', 'country', 'state', 'city', 'zip_code', 'phone_num',
                  'search_profile_security', 'two_fa_by_email', 'two_fa_by_app')

    def get_country(self, obj):
        countries_dict = dict(countries)
        if obj.country in countries_dict:
            return obj.country.code
        else:
            return None

    def get_profile_img(self, obj):
        if obj.profile_img:
            return "{0}".format(api_request_images(obj.profile_img))
        else:
            return ""


class ProfileBusinessSerializer(ProfileSerializer):
    incentive = serializers.ChoiceField(
        choices=Profile.INCENTIVE_CHOICES, required=True)
    skigit_incentive = serializers.SerializerMethodField()
    redemoption_instrucations = serializers.CharField(
        max_length=300, required=True)
    coupan_code = serializers.CharField(max_length=100, required=True)
    incetive_val = serializers.SerializerMethodField()
    contact_name = serializers.CharField(max_length=100, required=True)
    contact_email = serializers.EmailField(required=True)
    contact_phone = serializers.CharField(max_length=12, required=True)
    biller_name = serializers.CharField(max_length=100, required=True)
    payment_method = serializers.ChoiceField(
        choices=Profile.PAYMENT_CHOICES, required=True)
    biller_address1 = serializers.CharField(max_length=100, required=True)
    biller_address2 = serializers.CharField(max_length=100, required=True)
    payment_email = serializers.EmailField(required=True)
    coupan_image = serializers.SerializerMethodField()
    payment_user_name = serializers.CharField(max_length=35, required=True)
    business_type = serializers.ChoiceField(
        choices=Profile.BUSINESS_TYPE_CHOICES, required=True)
    custom_business_type = serializers.CharField(
        max_length=100, required=False)

    class Meta:
        model = Profile
        fields = ('user', 'profile_img', 'company_title', 'gender', 'birthdate', 'about_me', 'language', 'country',
                  'state', 'city', 'zip_code', 'phone_num', 'search_profile_security', 'incentive', 'skigit_incentive',
                  'redemoption_instrucations', 'coupan_code', 'incetive_val', 'contact_name', 'contact_email',
                  'contact_phone', 'biller_name', 'payment_method', 'biller_address1', 'biller_address2',
                  'payment_email', 'coupan_image',
                  'payment_user_name', 'business_type', 'custom_business_type')

    def get_skigit_incentive(self, obj):
        if obj.skigit_incentive and obj.incetive_val:
            value = obj.skigit_incentive
        else:
            value = "None offered at this time"
        return value

    def get_incetive_val(self, obj):
        if obj.incetive_val:
            value = obj.incetive_val
        else:
            value = 0
        return value

    def get_coupan_image(self, obj):
        if obj.coupan_image:
            return "{0}".format(api_request_images(obj.coupan_image))
        else:
            return ""


class ProfileNotificationSerializer(serializers.ModelSerializer):
    like_notify = serializers.BooleanField()
    follow_un_follow_notify = serializers.BooleanField()
    friends_request_notify = serializers.BooleanField()
    friends_accept_notify = serializers.BooleanField()
    plug_notify = serializers.BooleanField()
    un_plug_notify = serializers.BooleanField()
    skigit_notify = serializers.BooleanField()
    share_notify = serializers.BooleanField()

    class Meta:
        model = Profile
        fields = ('like_notify', 'follow_un_follow_notify', 'friends_request_notify', 'friends_accept_notify',
                  'plug_notify', 'un_plug_notify', 'skigit_notify', 'share_notify')


class BaseAPISerialier(serializers.Serializer):
    deviceToken = serializers.CharField(max_length=500)
    deviceType = serializers.ChoiceField(choices=DEVICE_TYPE_CHOICES,
                                         default='web')


class LoginSerializer(BaseAPISerialier):
    username = serializers.EmailField()
    password = serializers.CharField(max_length=20)


class TwoFaSerializer(serializers.Serializer):
    username = serializers.EmailField()
    two_fa_code = serializers.CharField(max_length=8)


class EmailSerializer(serializers.Serializer):
    username = serializers.EmailField()


class LoginResponseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="id")
    user_name = serializers.CharField(source="username", max_length=100)
    email = serializers.EmailField()
    profile_pic = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    profile_status = serializers.SerializerMethodField()
    token = serializers.SerializerMethodField()

    class Meta:
        fields = ('user_id', 'user_name', 'email', 'profile_pic', 'user_type',
                  'profile_status', 'token')

    def get_profile_pic(self, obj):
        profile = get_object_or_None(Profile, user__id=obj.id)
        if profile and profile.profile_img:
            profile_pic = api_request_images(profile.profile_img)
        else:
            profile_pic = None
        return profile_pic

    def get_user_type(self, obj):
        if is_user_business(obj):
            user_type = 'business'
        elif is_user_general(obj):
            user_type = 'general'
        else:
            user_type = ''
        return user_type

    def get_profile_status(self, obj):
        profile_status = get_profile_status(obj)
        profile_status = 'not-completed' if profile_status['message'] else 'completed'
        return profile_status

    def get_token(self, obj):
        # Later you change the simpleJWT token for more secure!
        token_obj, created = Token.objects.get_or_create(user=obj)
        token = "Token {0}".format(token_obj.key)
        return token


class PasswordResetEmailSerializer(BaseAPISerialier):
    email = serializers.EmailField()


class UserAccountDeleteSerializer(BaseAPISerialier, serializers.ModelSerializer):
    #email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('deviceToken', 'deviceType')


class ProfileFriendsInviteSerializer(serializers.Serializer):
    name = serializers.CharField()
    image = serializers.CharField()
    uid = serializers.IntegerField()
    username = serializers.CharField()
    status = serializers.CharField()
    title = serializers.CharField()


class ProfileFriendSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    uid = serializers.IntegerField(source='user_id')
    username = serializers.CharField(source='user.username')
    followers_count = serializers.SerializerMethodField()
    followed_by_me = serializers.SerializerMethodField()
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('uid', 'username', 'name', 'profile_image',
                  'followed_by_me', 'followers_count', 'online_status')

    def get_name(self, obj):
        return "{0}".format(obj.user.get_full_name().title())

    def get_profile_image(self, obj):
        request = self.context['request']
        if obj.profile_img:
            l_img = api_request_images(
                obj.profile_img, quality=99, format='PNG')
            """if request.build_absolute_uri('?').find('/api/v1/') >= 0:
                l_img = api_request_images(obj.profile_img, quality=99, format='PNG')
            else:
                l_img = "{0}".format(get_thumbnail(obj.profile_img, '35x35', quality=99, format='PNG').url)"""
        else:
            l_img = "{0}{1}".format(settings.STATIC_URL,
                                    'images/noimage_user.jpg')
        return l_img

    def get_followed_by_me(self, obj):
        followed = 0
        data = self.context['request'].query_params if self.context['request'].query_params else self.context['request'].data

        if obj:
            if 'user_id' in data and data['user_id']:
                user_id = data['user_id']
            elif 'user' in data and data['user'].is_authenticated:
                user_id = data['user'].id
            else:
                user_id = ''
            followed = 1 if user_id and Follow.objects.filter(user_id__id=user_id,
                                                              status=True,
                                                              follow__id=obj.user.id).exists() else followed
        return followed

    def get_followers_count(self, obj):
        return Follow.objects.filter(follow__id=obj.user.id,
                                     status=True).count()

    def get_online_status(self, obj):
        '''
            Show online status of the user!
        '''
        status = 'online' if obj.user.id in get_all_logged_in_users() else 'offline'
        return status


class BusinessLogoSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = BusinessLogo
        fields = ('id', 'logo')

    def get_logo(self, obj):
        if obj.logo:
            return "{0}".format(api_request_images(obj.logo))
            # return "{0}".format(get_thumbnail(obj.logo, "{0}x{1}".format(obj.logo.width, obj.logo.height)).url)
        else:
            return ""


class BusinessProfileDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    email = serializers.EmailField(source='user.email')
    username = serializers.CharField(source='user.username')
    #logo_img = BusinessLogoSerializer(many=True)
    logo_img = serializers.SerializerMethodField()
    incetive_val = serializers.SerializerMethodField()
    incentive_detail = serializers.SerializerMethodField()
    incentive_popup_header = serializers.SerializerMethodField()
    incentive_img = serializers.SerializerMethodField()
    company_title = serializers.CharField()

    class Meta:
        model = Profile
        fields = ('user_id', 'email', 'username', 'incetive_val', 'logo_img', 'incentive_detail', 'incentive_popup_header', 'incentive_img',
                  'company_title')

    def get_logo_img(self, obj):
        logo_images = obj.logo_img.filter(is_deleted=False)
        images = [{'id': logo.id,
                   'logo': "{0}".format(get_thumbnail(logo.logo,
                                                      "{0}x{1}".format(logo.logo.width,
                                                                       logo.logo.height)).url)}
                  for logo in logo_images]
        return images

    def get_incetive_val(self, obj):
        value = obj.incetive_val if obj.incentive else None
        return value

    def get_incentive_detail(self, obj):
        value = 'This maker is not offering any Skigit incentives at this time. Check back later!'
        value = obj.skigit_incentive if obj.skigit_incentive else value
        return value

    def get_incentive_img(self, obj):
        value = 'images/icons/crud_happy_icon.png' if obj.skigit_incentive else 'images/icons/crud_icon.png'
        value = '{0}{1}'.format(settings.STATIC_HOST_URL, value)
        return value

    def get_incentive_popup_header(self, obj):
        value = 'Rats!'
        value = 'Awesome' if obj.skigit_incentive else value
        return value


class ExtraProfileImageSerializer(serializers.ModelSerializer):
    profile_img = serializers.SerializerMethodField()

    class Meta:
        model = ExtraProfileImage
        fields = ('id', 'profile_img')

    def get_profile_img(self, obj):
        if obj.profile_img:
            return "{0}".format(api_request_images(obj.profile_img))
            # return "{0}".format(get_thumbnail(obj.profile_img, "{0}x{1}".format(obj.profile_img.width,
            #                                                                     obj.profile_img.height)).url)
        else:
            return ""


class ProfileUrlSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfileUrl
        fields = ('url1', 'disc1', 'url2', 'disc2', 'url3',
                  'disc3', 'url4', 'disc4', 'url5', 'disc5')


class SperkListSerializer(serializers.ModelSerializer):
    business_logo = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    owner = serializers.IntegerField(source='user_id')
    name = serializers.SerializerMethodField()
    incentive = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('logo', 'owner', 'name', 'company_title',
                  'business_logo', 'incentive')

    def get_incentive(self, obj):
        value = obj.incentive if obj.incentive else 0
        return value

    def get_logo(self, obj):
        logo_url = ''
        if obj.logo_img.filter(is_deleted=False).exists():
            logo = obj.logo_img.filter(is_deleted=False).all()[0].logo
            logo_url = api_request_images(logo, quality=99, format='PNG')
        return logo_url

    def get_business_logo(self, obj):
        logo_id = 0
        try:
            if obj.logo_img.filter(is_deleted=False).exists():
                logo_id = obj.logo_img.filter(is_deleted=False).all()[0].id
        except:
            pass
        return logo_id

    def get_name(self, obj):
        name = ''

        if obj.company_title:
            name = obj.company_title.title()
        elif obj.user.get_full_name():
            name = obj.user.get_full_name().title()
        else:
            name = obj.user.username.title()
        return name


class CustomTokenObtainSerializer(serializers.Serializer):
    username_field = User.USERNAME_FIELD

    default_error_messages = {
        'no_active_account': _('deactivated'),
        'no_account': _('no account'),
        'wrong_password': _('wrong password'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField()

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            'password': attrs['password'],
        }
        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)

        # Prior to Django 1.10, inactive users could be authenticated with the
        # default `ModelBackend`.  As of Django 1.10, the `ModelBackend`
        # prevents inactive users from authenticating.  App designers can still
        # allow inactive users to authenticate by opting for the new
        # `AllowAllUsersModelBackend`.  However, we explicitly prevent inactive
        # users from authenticating to enforce a reasonable policy and provide
        # sensible backwards compatibility with older Django versions.
        data = {}
        data["data"] = {}
        if self.user is None:
            data["status_code"] = 401
            try:
                user = User.objects.get(
                    username=authenticate_kwargs["username"])
                if user.check_password(authenticate_kwargs["password"]):
                    data["message"] = self.error_messages['no_active_account']
                else:
                    data["message"] = self.error_messages['wrong_password']
            except:
                data["message"] = self.error_messages['no_account']

        else:
            data["message"] = "activated"
            data["status_code"] = 200
        return data

    @classmethod
    def get_token(cls, user):
        raise NotImplementedError(
            'Must implement `get_token` method for `TokenObtainSerializer` subclasses')


class CustomTokenObtainPairSerializer(CustomTokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user:
            refresh = self.get_token(self.user)
            data["data"]['refresh'] = str(refresh)
            data["data"]['access'] = str(refresh.access_token)

        return data
