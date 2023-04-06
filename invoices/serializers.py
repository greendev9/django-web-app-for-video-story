from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import serializers

from invoices.models import *

class PaymentMethodCardSerializer(serializers.ModelSerializer):
    card = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ('user', 'c_image_url', 'card', 'cardholder_name')

    def get_card(self, obj):
        return str('%06d*****%04d') % (int(obj.first_6), int(obj.last_4))

class PaymentMethodPaypalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        fields = ('user', 'c_image_url', 'email')

class BusinessLogoInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = BusinessLogoInvoice
        fields = ('total_logo_count', 'user_total_due')

class WebLinkInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebLinkInvoice
        fields = ('link_total_count', 'link_total_due')

class PluginInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = PluginInvoice
        fields = ('plugin_total_count', 'plugin_total_amount')

class PostInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostInvoice
        fields = ('post_total_count', 'post_total_amount')

class ShareInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShareInvoice
        fields = ('total_share_count', 'share_total_amount')

class EmbedInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmbedInvoice
        fields = ('embed_total_count', 'embed_total_amount')

class InvoiceDetailSerializer(serializers.Serializer):
    current_month = serializers.IntegerField()
    year = serializers.IntegerField()
    month = serializers.CharField()
    month_num = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    logo_detail = BusinessLogoInvoiceSerializer()
    link_detail = WebLinkInvoiceSerializer()
    plug_detail = PluginInvoiceSerializer()
    post_detail = PostInvoiceSerializer()
    share_detail = ShareInvoiceSerializer()
    embed_detail = EmbedInvoiceSerializer()
    card_type = serializers.CharField()
    card_detail = serializers.CharField()
    card_img = serializers.CharField()
    invoice_billing_id = serializers.IntegerField(source='inv.id')

