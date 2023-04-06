from user.models import BusinessLogo

from django.contrib.auth.models import User
from django.db import models

from core.models import BaseModel
from skigit.models import VideoDetail


class BusinessLogoInvoice(BaseModel):
    """ Business Logo Invoice
    """

    logo_user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='logo_viewer_user',
        verbose_name='Business Logo User'
    )
    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='business_logo_user',
        verbose_name='Business Logo Visitor'
    )
    business_logo = models.ForeignKey(
        BusinessLogo,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="BusinessLogo"
    )
    logo_count = models.IntegerField(
        'Logo PPV Count',
        default=0
    )
    logo_total_amount = models.DecimalField(
        'Due Amount($)',
        max_digits=9,
        decimal_places=2,
        blank=True,
        default=0.00
    )
    logo_is_paid = models.BooleanField(
        'Amount Paid',
        default=False
    )
    total_logo_count = models.IntegerField(
        "Total Count (PPV)",
        default=0
    )
    user_total_due = models.DecimalField(
        'Total Due Amount($)',
        max_digits=9,
        decimal_places=2,
        blank=True,
        default=0.00
    )
    billing_month = models.DateField(
        auto_created=True,
        auto_now_add=True,
        editable=False
    )

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Business Logo Invoice"
        verbose_name_plural = "Business Logo Invoices"


class WebLinkInvoice(BaseModel):
    """ Web Link Invoice
    """

    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='link_visitor_user',
        verbose_name='Business User'
    )
    web_link_user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='web_link_user',
        verbose_name='Web Link User'
    )
    web_link = models.URLField(
        'Awesome Company Links',
        null=True,
        blank=True
    )
    link_count = models.IntegerField('Links Count', default=0)
    link_due_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                          default=0.00)
    link_total_due = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                         default=0.00)
    link_total_count = models.IntegerField('Total Count', default=0)
    link_is_paid = models.BooleanField('Amount Paid', default=False)

    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Web link Invoice"
        verbose_name_plural = "Web link Invoices"


class PluginInvoice(BaseModel):
    """ Web Link Invoice
    """

    skigit_user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='skigit_plugin_user',
        verbose_name='Skigit Logo User'
    )
    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='business_plugin_user',
        verbose_name='User'
    )
    plugin_ski = models.ForeignKey(
        VideoDetail,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='primary_ski',
        verbose_name='Plugged Skigit'
    )
    primary_ski = models.ForeignKey(
        VideoDetail,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='plug_ski',
        verbose_name='Skigit'
    )
    plugin_count = models.IntegerField('Plugin Count', blank=True, default=0)
    current_plugin_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                                default=0.00)
    plugin_total_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                              default=0.00)
    plugin_total_count = models.IntegerField('Total Count', blank=True, default=0)
    plug_is_paid = models.BooleanField('Amount Paid', default=False)

    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Plugin Invoice"
        verbose_name_plural = "Plugin Invoices"


class LearnMoreInvoice(BaseModel):
    """ Learn More Invoice
    """

    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='business_learn_more_user',
        verbose_name='Learn More User'
    )

    learn_ski = models.ForeignKey(
        VideoDetail,
        models.SET_NULL,
        blank=True,
        null=True
    )

    learn_count = models.IntegerField('Learn More Count', blank=True, null=True)
    learn_due_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True, default=0.00)
    learn_total_due = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True, default=0.00)
    current_learn_amount = models.DecimalField('Current Learn more Amount($)', max_digits=9, decimal_places=2, blank=True, default=0.00)
    learn_total_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True, default=0.00)
    learn_total_count = models.IntegerField('Total Count', blank=True, null=True)
    learn_is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Learn More Link Invoice"
        verbose_name_plural = "Learn More Link Invoices"


class PostInvoice(BaseModel):
    """ Social post invoice
    """

    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='business_post_user',
        verbose_name='Post User'
    )
    logo_user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='b_logo_user',
        verbose_name='Logo User'
    )
    post_ski = models.ForeignKey(
        VideoDetail,
        models.SET_NULL,
        blank=True,
        null=True
    )
    post_count = models.IntegerField('Post Count', blank=True, null=True)
    skigit_post_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    post_total_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True, default=0.00)
    post_total_count = models.IntegerField('Total Count', blank=True, null=True)
    social_network_type = models.CharField('Social Network Type', max_length=500, blank=True, null=True)
    post_is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Post Invoice"
        verbose_name_plural = "Post Invoices"


class ShareInvoice(BaseModel):
    """ Share Invoice
    """
    skigit_user = models.ForeignKey(User, blank=True, null=True, related_name='skigit_share_user',
                                    verbose_name='Skigit User',on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, related_name='business_share_user',
                             verbose_name='User',on_delete=models.CASCADE)
    share_ski = models.ForeignKey(VideoDetail, blank=True, null=True,on_delete=models.CASCADE)
    share_count = models.IntegerField('Share Count', blank=True, null=True)
    share_total_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    skigit_share_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                              default=0.00)
    total_share_count = models.IntegerField('Total Count', blank=True, null=True)
    share_is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Share Invoice"
        verbose_name_plural = "Share Invoices"


class EmbedInvoice(BaseModel):
    """
        External Embed Invoice
    """
    skigit_user = models.ForeignKey(User, blank=True, null=True, related_name='skigit_embed_user',
                                    verbose_name='Skigit User',on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, related_name='embed_business_user',
                             verbose_name='Business User',on_delete=models.CASCADE)
    embed_ski = models.ForeignKey(VideoDetail, blank=True, null=True,on_delete=models.CASCADE)
    embed_count = models.IntegerField('Embed Count', blank=True, null=True)
    embed_total_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    skigit_embed_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                              default=0.00)
    embed_total_count = models.IntegerField('Total Count', blank=True, null=True)
    embed_is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Embed External Invoice"
        verbose_name_plural = "Embed External Invoices"


class InternalEmbedInvoice(BaseModel):
    """
        Internal Embed Invoice
    """
    skigit_user = models.ForeignKey(User, blank=True, null=True, related_name='skigit_internal_embed_user',
                                    verbose_name='Skigit User',on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, related_name='internal_embed_business_user',
                             verbose_name='Business User',on_delete=models.CASCADE)
    embed_ski = models.ForeignKey(VideoDetail, blank=True, null=True,on_delete=models.CASCADE)
    embed_count = models.IntegerField('Embed Count', blank=True, null=True)
    embed_total_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    skigit_embed_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                              default=0.00)
    embed_total_count = models.IntegerField('Total Count', blank=True, null=True)
    embed_is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Internal Embed Invoice"
        verbose_name_plural = "Internal Embed Invoices"


class VisitCharges(BaseModel):
    """ Costing For Payment Module.
    """

    user = models.ForeignKey(User, null=True, blank=True, related_name="superuse_payment", verbose_name='User',on_delete=models.CASCADE)
    logo_charge = models.DecimalField('Logo PPV Charge', max_digits=9, decimal_places=2, blank=True, default=0.29)
    link_charge = models.DecimalField('Web Link Charge', max_digits=9, decimal_places=2, blank=True, default=1.99)
    plug_charge = models.DecimalField('Plugin Charge', max_digits=9, decimal_places=2, blank=True, default=0.29)
    post_charge = models.DecimalField('Post Charge', max_digits=9, decimal_places=2, blank=True, default=0.79)
    share_charge = models.DecimalField('Share Charge', max_digits=9, decimal_places=2, blank=True, default=0.49)
    embed_charge = models.DecimalField('Embed Charge', max_digits=9, decimal_places=2, blank=True, default=49.0)

    class Meta:
        verbose_name = "Business Charge"
        verbose_name_plural = "Business Charges"


class Invoice(BaseModel):
    """ Invoice Details for user.
    """

    user = models.ForeignKey(User,
        models.SET_NULL, null=True, blank=True, related_name="invoice_user", verbose_name='User')
    customer_id = models.CharField('Customer id', max_length=100)
    customer_location = models.CharField('Customer Location', max_length=250, blank=True, null=True)
    type = models.CharField('Type', max_length=50, blank=True, null=True)
    payment_method_token = models.CharField('Customer token', max_length=300)
    c_image_url = models.URLField('Card Type Image', max_length=200, blank=True, null=True)

    # payPal Fields
    email = models.EmailField('PayPal Email', blank=True, null=True)
    billing_agreement_id = models.CharField('Billing Agreement ID', max_length=150, blank=True, null=True)

    # Credit Card Fields
    last_4 = models.PositiveSmallIntegerField('Last 4 Numbers', blank=True, null=True)
    first_6 = models.PositiveIntegerField('first 6 Numbers (bin)', blank=True, null=True)
    cardholder_name = models.CharField('Card Holder Name', max_length=250, blank=True, null=True)
    debit = models.CharField('Debit', max_length=300, blank=True, null=True)
    issuing_bank = models.CharField('Issuing Bank', max_length=250, blank=True, null=True)
    country_of_issuance = models.CharField('Country of Issuance', max_length=250, blank=True, null=True)
    card_status = models.CharField('Card Status', max_length=250, blank=True, null=True)
    cvv_response_code = models.CharField('CVV Response Code', max_length=10, blank=True, null=True)
    currency_iso_code = models.CharField('Currency iso Code', max_length=10, blank=True, null=True)
    credit_card_type = models.CharField('Credit/Debit Card Type', max_length=200, blank=True, null=True)
    is_deleted = models.BooleanField('Is Credit Card/ PayPal Account Deleted', default=False)
    merchant_account_id = models.URLField('Merchant Account id', blank=True, null=True)
    unique_number_identifier = models.CharField('Unique Identifier Number', max_length=500, blank=True, null=True)
    processor_response_code = models.CharField('Processor Response Code', max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Invoice Vault"
        verbose_name_plural = "Invoices Vault"


class InvoiceBilling(BaseModel):
    """ Billing Detail for user.
    """

    PAYMENT_STATUS = (
        (False, 'Pending'),
        (True, 'Payed'),
    )

    PAYMENT_CHOICE = (
        ('0', 'PayPalAccount'),
        ('1', 'CreditCard'),
    )

    user_id = models.ForeignKey(User,
        models.SET_NULL, null=True, blank=True, related_name="billing_user", verbose_name='User')
    invoice = models.ForeignKey(Invoice, related_name='invoices_billing', verbose_name='Invoice Vault',on_delete=models.CASCADE)
    pay_amount = models.DecimalField('Payable Amount', max_digits=9, decimal_places=2, blank=True, default=0.0)
    payed_amount = models.DecimalField('Payed Amount', max_digits=9, decimal_places=2, blank=True, default=0.0)
    payment_status = models.BooleanField('Payment Received', default=False, choices=PAYMENT_STATUS)
    pay_method = models.CharField('Payment Method', max_length=5, default='0', choices=PAYMENT_CHOICE)
    pay_mnth = models.CharField('Pay Month', max_length=2)
    pay_yr = models.CharField('Pay Year', max_length=4)
    transaction_id = models.CharField('Transaction id', max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Billing Info"
        verbose_name_plural = "Billing Info"


class ViewInvoice(BaseModel):
    skigit_user = models.ForeignKey(User, blank=True, null=True, related_name='business_skigit_view_user',
                                    verbose_name='Skigit User',on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, related_name='skigit_view_user',
                             verbose_name='User',on_delete=models.CASCADE)
    view_ski = models.ForeignKey(VideoDetail, blank=True, null=True,on_delete=models.CASCADE)
    view_count = models.IntegerField('View Count', blank=True, null=True)
    skigit_view_amount = models.DecimalField('Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                              default=0.00)
    view_total_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    total_view_count = models.IntegerField('Total Count', blank=True, null=True)
    view_is_paid = models.BooleanField('Amount Paid', default=False)

    VIEW_CHOICES = (
        (0, 'Detail'),
        (1, 'Main'),
    )

    view_page = models.IntegerField(default=0, choices=VIEW_CHOICES)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.skigit_user.username

    class Meta:
        verbose_name = "View Invoice"
        verbose_name_plural = "View Invoices"


class MonthlyLogoInvoice(BaseModel):
    user = models.ForeignKey(User, blank=True, null=True, verbose_name='User',on_delete=models.CASCADE)
    logo_amount = models.DecimalField('Logo Amount($)', max_digits=9, decimal_places=2, blank=True,
                                              default=0.00)
    logo_total_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    total_logo_count = models.IntegerField('Total Count', blank=True, null=True)
    is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Monthly Logo Invoice"
        verbose_name_plural = "Monthly Logo Invoices"


class MonthlySkigitInvoice(BaseModel):
    user = models.ForeignKey(User, blank=True, null=True, verbose_name='User',on_delete=models.CASCADE)
    skigit = models.ForeignKey(VideoDetail, blank=True, null=True,on_delete=models.CASCADE)
    skigit_amount = models.DecimalField('Skigit Amount($)', max_digits=9, decimal_places=2, blank=True,
                                              default=0.00)
    skigit_total_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    total_skigit_count = models.IntegerField('Total Count', blank=True, null=True)
    is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Monthly Skigit Invoice"
        verbose_name_plural = "Monthly Skigit Invoices"


class DonateInvoice(BaseModel):
    """ Donate invoice
    """

    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='business_user',
        verbose_name='Business User'
    )
    video = models.ForeignKey(
        VideoDetail,
        models.SET_NULL,
        blank=True,
        null=True
    )
    donate_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    donate_is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Donate Invoice"
        verbose_name_plural = "Donate Invoices"

class QRCodeInvoice(BaseModel):
    """ QR Code Invoice
    """

    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='businessUser',
        verbose_name='Business User'
    )
    qrcode_count = models.IntegerField('QR Code Count',default=0)
    qrcode_amount = models.DecimalField('Total Due Amount($)', max_digits=9, decimal_places=2, blank=True,
                                             default=0.00)
    qrcode_is_paid = models.BooleanField('Amount Paid', default=False)
    billing_month = models.DateField(auto_created=True, auto_now_add=True, editable=False)
  

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "QR Code Invoice"
        verbose_name_plural = "QR Code Invoices"