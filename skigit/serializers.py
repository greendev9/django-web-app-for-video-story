from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.conf import settings
from django.urls import reverse
from sorl.thumbnail import get_thumbnail as TN

from rest_framework import serializers
from skigit.models import (VideoDetail, Profile, Like,
                           BusinessLogo, Category, SubjectCategory,
                           Video, Donation, Incentive, BugReport, VideoDetail, InappropriateSkigitReason,
                           CopyRightInfringement, Favorite)
from social.models import Share, Follow

from user.serializers import BaseAPISerialier, BusinessLogoSerializer, api_request_images
from core.serializers import SubjectCategorySerializer
from core.utils import get_object_or_None, check_valid_url

def get_request_data(context):
    data = {}
    if 'request' in context:
        user_id = context['request'].user.id if context['request'].auth else 0
        if context['request'].query_params:
            data = context['request'].query_params.copy()
        else:
            data = context['request'].data.copy()
        if user_id:
            data.update(user_id=user_id)
    if not data:
        data = context
    return data

class VideoDetailSerializer(serializers.ModelSerializer):

    category = serializers.SerializerMethodField()
    category_slug = serializers.SerializerMethodField()
    subject_category = serializers.SerializerMethodField()
    subject_category_slug = serializers.SerializerMethodField()
    business_logo_url = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    profile_imgs = serializers.SerializerMethodField()
    video_playback_id = serializers.SerializerMethodField()
    video_like = serializers.SerializerMethodField()
    video_plug = serializers.SerializerMethodField()
    video_share = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    favourite_by_me = serializers.SerializerMethodField()
    followed_by_me = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    class Meta:
        model = VideoDetail
        fields = ('pk', 'id', 'title', 'category', 'category_slug', 'subject_category', 'subject_category_slug', 'business_logo',
                  'business_logo_url', 'thumbnail', 'owner', 'username', 'bought_at_url',
                  'profile_imgs', 'skigit_id', 'made_by', 'video_playback_id', 'liked_by_me', 'favourite_by_me', 'followed_by_me',
                  'video_like', 'why_rocks', 'video_plug', 'video_share', 'view_count', 'created_date', 'is_plugged',
                  'updated_date')

    def get_business_logo_url(self, obj):
        logo_url = ""

        if obj.made_by:
            if obj.business_logo:
                if obj.business_logo.is_deleted is False:
                    logo_url = obj.business_logo.logo
                else:
                    us_profile = Profile.objects.get(user=obj.made_by)
                    if us_profile.logo_img.filter(is_deleted=False).all().count() > 0:
                        logo_url = us_profile.logo_img.filter(is_deleted=False).all()[0].logo
        if logo_url:
            #logo_url = TN(logo_url, "x200").url
            logo_url = api_request_images(logo_url, quality=99, format='PNG')
        return logo_url

    def get_thumbnail(self, obj):
        try:
            if obj:
                return obj.skigit_id.thumbnails.all()[0].get_absolute_url()
        except:
            pass
        return ''

    def get_username(self, obj):
        if obj.skigit_id:
            return obj.skigit_id.user.username
        return ''

    def get_owner(self, obj):
        if obj.skigit_id:
            return obj.skigit_id.user.id
        return ''

    def get_profile_imgs(self, obj):
        if obj:
            host = ''.join(settings.HOST)[:-1]
            try:
                profile = Profile.objects.filter(
                    user_id=obj.skigit_id.user
                ).select_related('profile_img').first()
            except FieldError:
                profile = Profile.objects.filter(
                    user_id=obj.skigit_id.user
                ).select_related('cover_img').first()
            if profile.profile_img:
                return host + "{0}".format(profile.profile_img.url)
            elif profile.cover_img:
                return host + "{0}".format(profile.cover_img.url)
            return ''
        return ''

    def get_category(self, obj):
        if obj.category:
            return obj.category.cat_name
        return ''

    def get_category_slug(self, obj):
        if obj.category:
            return obj.category.cat_slug
        return ''

    def get_subject_category(self, obj):
        if obj.subject_category:
            return obj.subject_category.sub_cat_name
        return ''

    def get_subject_category_slug(self, obj):
        if obj.subject_category:
            return obj.subject_category.sub_cat_slug
        return ''

    def get_video_playback_id(self, obj):
        if obj.skigit_id:
            return obj.skigit_id.video_id
        return ''

    def get_video_like(self, obj):
        if obj:
            return Like.objects.filter(skigit=obj.skigit_id, status=True).count()
        return '0'

    def get_video_plug(self, obj):
        if obj:
            return VideoDetail.objects.filter(plugged_skigit=obj.skigit_id,
                                              is_plugged=True, status=1).count()
        return '0'

    def get_video_share(self, obj):
        if obj:
            return Share.objects.filter(skigit_id=obj, is_active=True).count()
        return '0'

    ##Later: Need to use this in template to find the like or not quickly
    def get_liked_by_me(self, obj):
        liked = 0
        data = get_request_data(self.context)

        if obj:
            if 'user_id' in data and data['user_id']:
                user_id = data['user_id']
            elif 'user' in data and data['user'].is_authenticated:
                user_id = data['user'].id
            else:
                user_id = ''
            liked = 1 if user_id and Like.objects.filter(user_id__id=user_id,
                                                         status=True,
                                                         skigit__id=obj.skigit_id.id).exists() else liked
        return liked

    ##Later: Need to use this in template to find the fav or not quickly
    def get_favourite_by_me(self, obj):
        favourite = 0
        data = get_request_data(self.context)
        if obj:
            if 'user_id' in data and data['user_id']:
                user_id = data['user_id']
            elif 'user' in data and data['user'].is_authenticated:
                user_id = data['user'].id
            else:
                user_id = ''
            favourite = 1 if user_id and Favorite.objects.filter(user_id__id=user_id,
                                                         status=1,
                                                         skigit__id=obj.skigit_id.id).exists() else favourite
        return favourite

    ##Later: Need to use this in template to find the follow user or not quickly
    def get_followed_by_me(self, obj):
        followed = 0
        data = get_request_data(self.context)

        if obj:
            if 'user_id' in data and data['user_id']:
                user_id = data['user_id']
            elif 'user' in data and data['user'].is_authenticated:
                user_id = data['user'].id
            else:
                user_id = ''
            followed = 1 if user_id and Follow.objects.filter(user_id__id=user_id,
                                                              status=True,
                                                              follow__id=obj.skigit_id.user.id).exists() else followed
        return followed


class PluginVideoSerializer(VideoDetailSerializer):
    second_level_plugins = VideoDetailSerializer(many=True)
    second_level_plugins_count = serializers.IntegerField()

    class Meta:
        model = VideoDetail
        fields = ('pk', 'id', 'title', 'category', 'category_slug', 'subject_category', 'subject_category_slug', 'business_logo',
                  'business_logo_url', 'thumbnail', 'owner', 'username', 'bought_at_url',
                  'profile_imgs', 'skigit_id', 'made_by', 'video_playback_id', 'liked_by_me', 'favourite_by_me', 'followed_by_me',
                  'video_like', 'why_rocks', 'video_plug', 'video_share', 'view_count', 'created_date', 'is_plugged',
                  'updated_date', 'second_level_plugins', 'second_level_plugins_count')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = '__all__'

class IncentiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incentive
        fields = '__all__'

class LikedSkigitSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    subject_category = SubjectCategorySerializer()
    share_skigit = VideoSerializer()
    plugged_skigit = VideoSerializer()
    donate_skigit = DonationSerializer()
    incentive = IncentiveSerializer()
    business_logo = BusinessLogoSerializer()

    class Meta:
        model = VideoDetail
        fields = '__all__'

class BugReportSerializer(serializers.ModelSerializer):
    video_id = serializers.IntegerField(required=False)
    bug_description = serializers.CharField(required=True)

    class Meta:
        model = BugReport
        fields = ('user', 'video_id', 'bug_page_url', 'bug_description', 'bug_repeated')

    def create(self, validated_data):
        user = validated_data.get('user', None)
        bug_page_url = validated_data.get('bug_page_url', '')
        bug_repeated = validated_data.get('bug_repeated', '0')

        bug_repeated = True if bug_repeated == '1' else False
        bug_report = BugReport(bug_description=validated_data.get('bug_description', ''),
                               bug_repeated=bug_repeated)

        if validated_data.get('video_id', ''):
            bug_report.skigit_id = get_object_or_None(VideoDetail, pk=validated_data.get('video_id'))
            bug_page_url = '{0}{1}'.format(settings.HOST,
                                           reverse('skigit_data', kwargs={'pk': validated_data.get('video_id')}))

        bug_report.bug_page_url = bug_page_url
        bug_report.save()
        if user:
            bug_report.user = user.username
        bug_report.bug_title = 'Bug#{}'.format(bug_report.id)
        bug_report.save()
        return bug_report

class ManageLikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Like
        fields = ('user',)

class InappropriateReasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = InappropriateSkigitReason
        fields = ('id', 'reason_slug', 'reason_title')

class CopyrightInfringementSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    signature = serializers.CharField(required=True)
    zip_code = serializers.IntegerField(required=True, min_value=10000, max_value=999999999999,
                                        error_messages={'blank': 'Please enter zip code.',
                                                        'invalid': 'Please enter between 5 and 12 numbers only.'})
    country = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)

    class Meta:
        model = CopyRightInfringement
        fields = ('user_id', 'urls', 'submitter_request', 'address', 'city', 'state', 'zip_code', 'country',
                  'phone', 'email', 'full_name', 'signature','skigit_id')

    def create(self, validated_data):
        user_profile = Profile.objects.get(user__id=validated_data.get('user_id'))
        copy_right = CopyRightInfringement(user_id=user_profile.user,
                                           submitted_by=user_profile,
                                           urls=validated_data.get('urls'),
                                           submitter_request=validated_data.get('submitter_request'),
                                           address=validated_data.get('address'),
                                           city=validated_data.get('city'),
                                           state=validated_data.get('state'),
                                           zip_code=validated_data.get('zip_code'),
                                           country=validated_data.get('country'),
                                           phone=validated_data.get('phone'),
                                           email=validated_data.get('email'),
                                           full_name=validated_data.get('full_name'),
                                           signature=validated_data.get('signature'),
                                           skigit_id=validated_data.get('skigit_id'))
        copy_right.save()
        # set the skigit under open copyright infringement
        VideoDetail.objects.filter(pk=validated_data.get('skigit_id')).update(copyright_skigit=0)
        return copy_right

class VideoUploadSerializer(serializers.Serializer):
    # sample = <MultiValueDict: {'file_on_server': [<TemporaryUploadedFile: VID_20190203_081225.mp4 (video/mp4)>]}> <QueryDict: {'title': ['Kalyanam'], 'why_rocks': ['It is y fav!'], 'category': ['1'], 'subject_category': ['1'], 'made_by': ['6'], 'made_by_option': [''], 'bought_at': ['http://www.youtube.com/'], 'add_logo': ['1'], 'receive_donate_sperk': ['2'], 'select_logo': ['8'], 'donate_sperk': ['undefined']}>
    title = serializers.CharField()
    category = serializers.IntegerField()
    subject_category = serializers.IntegerField()
    made_by = serializers.IntegerField(required=False)
    made_by_option = serializers.CharField(required=False)
    bought_at = serializers.CharField()
    add_logo = serializers.IntegerField(required=False)
    why_rocks = serializers.CharField()
    receive_donate_sperk = serializers.IntegerField(required=False)
    donate_group = serializers.IntegerField(required=False)
    select_logo = serializers.IntegerField(required=False)
    #donate_sperk = serializers.IntegerField()
    video_link = serializers.URLField(required=False)
    file_on_server = serializers.FileField(required=False)

    def validate_bought_at(self, value):
        url_valid = False
        if value:
            url_valid = check_valid_url(value)
        if not url_valid:
            raise serializers.ValidationError("I Bought My Awesome URL is invalid. Please enter a valid URL.")
        return value


class VideoDirectUploadSerializer():
    file_on_server = serializers.FileField(required=False)
