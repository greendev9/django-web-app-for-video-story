from rest_framework import serializers

from .models import Friend, Notification

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        publish_fields = ['message', 'skigit_id','from_user', 'is_read',
                          'msg_type', 'create_date']


class GeneralNotificationsAPISerializer(serializers.Serializer):
    id = serializers.IntegerField()
    message_type = serializers.CharField()
    from_user_name = serializers.CharField()
    from_user_id = serializers.IntegerField()
    is_read = serializers.IntegerField()
    video_title = serializers.CharField(required=False)
    video_id = serializers.IntegerField(required=False)
    plug_video_title = serializers.CharField(required=False)
    header = serializers.CharField(required=False)
    plug_video_id = serializers.IntegerField(required=False)
    view_general = serializers.CharField(required=False)
    from_user_type = serializers.CharField(required=False)
    created_date = serializers.DateTimeField()


class FriendNotificationsAPISerializer(serializers.Serializer):
    to_user = serializers.IntegerField()
    name = serializers.CharField()
    profile_img = serializers.CharField()
    status = serializers.IntegerField()
    username = serializers.CharField()
