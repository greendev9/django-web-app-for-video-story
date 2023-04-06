from rest_framework import serializers
from sperks.models import Donation

class DonationSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = ('id', 'value')

    def get_value(self, obj):
        return obj.ngo_name