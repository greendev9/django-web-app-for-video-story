from datetime import datetime, timedelta
import uuid
from io import BytesIO
import random

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from django.core.files import File

import qrcode
from PIL import Image
from sorl.thumbnail import get_thumbnail
from django_countries.fields import CountryField

from core.models import BaseModel


DEVICE_TYPE_CHOICES = [
    ('web', 'Website'),
    ('ios', 'IOS'),
    ('android', 'Android')
]

QR_SCAN_SECURITY_CODES = ['OJLNFLGM', 'MDUAGXQU', 'ZZPDFERV',
                          'TOTWEHGO', 'QDCSRONK', 'FWEJUTWC',
                          'HFWHHLSZ', 'CNZSXTYP', 'ODCBYKCN',
                          'RBAJRKSI', 'NPELMJGA', 'RWPJWTUT',
                          'NCHFJHTJ', 'CEKRSNHX', 'WYRBZDCS',
                          'RQLLTUMC', 'TJYEWTTJ', 'LMTCGJVD',
                          'LQGENBIH', 'LRMJVAFW', 'QLXTGHYQ',
                          'JCYBWCTP', 'FXBUUZWK', 'DZJRTZOH',
                          'OHZKQLGS', 'KFTVKKOK', 'IDDRJTCM',
                          'ALRCWDPF', 'WSRFGKKZ', 'SGAPNFVV']

PROFILE_DEACTIVATE_REASON_CHOICES = [
    ('', '--------'),
    ('not-interest', "Skigit content doesn't interest me."),
    ('not-user-friendly', 'The Skigit website or app is not user-friendly and easy to use.'),
    ('no-time', "I don't have the time to use Skigit."),
    ('lowered-self-esteem', 'Skigit has lowered my self-esteem.'),
    ('not-like-ideas', "I don't like the idea of teaming up with Brands and non-profit organizations."),
    ('other', 'Other'),
]

def is_user_business(user):
    """
        Checks whether user is Business User
    """
    return user.groups.filter(name=settings.BUSINESS_USER).exists()

def is_verified_business_user(user):
    """
        Checks whether user is Business User
    """
    return user.profile.business_verified

class BusinessLogo(BaseModel):
    """ Comment: Business Logo Model
    """
    logo = models.ImageField(
        upload_to="skigit/logo/%y/%m/%d",
        blank=True,
        null=True
    )
    is_deleted = models.BooleanField(
        default=False,
        blank=False
    )

    def __str__(self):
        return "{}".format(self.id)


class ProfileImg(BaseModel):
    profile_img = models.ImageField(upload_to="skigit/profile/%y/%m/%d",
                                    blank=True, null=True)
    is_active = models.BooleanField(default=True)


class ExtraProfileImage(BaseModel):
    profile_img = models.ImageField(upload_to="skigit/profile/%y/%m/%d",
                                    blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return "{}".format(self.profile_img)

class BusinessDoc(BaseModel):
    doc = models.FileField(upload_to="skigit/doc/%y/%m/%d",
                                    blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return "{}".format(self.doc)
    
class ProfileUrl(models.Model):
    disc1 = models.CharField(max_length=30, blank=True, null=True)
    url1 = models.URLField(blank=True, null=True)
    disc2 = models.CharField(max_length=30, blank=True, null=True)
    url2 = models.URLField(blank=True, null=True)
    disc3 = models.CharField(max_length=30, blank=True, null=True)
    url3 = models.URLField(blank=True, null=True)
    disc4 = models.CharField(max_length=30, blank=True, null=True)
    url4 = models.URLField(blank=True, null=True)
    disc5 = models.CharField(max_length=30, blank=True, null=True)
    url5 = models.URLField(blank=True, null=True)
    user = models.ForeignKey(User, related_name="User",on_delete=models.CASCADE)


class Profile(BaseModel):
    GENDER_MALE = 0
    GENDER_FEMALE = 1

    INCENTIVE_NO = 0
    INCENTIVE_YES = 1

    PAYMENT_CHOICES = (
        ('0', 'PayPal'),
        ('1', 'Credit/Debit Card'),
    )

    GENDER_CHOICES = [(GENDER_MALE, 'Male'), (GENDER_FEMALE, 'Female')]
    INCENTIVE_CHOICES = [(INCENTIVE_NO, 'No'), (INCENTIVE_YES, 'Yes')]
    LANGUAGE_CHOICES = [('', 'Select Language'), ("ENG", "English"),
                        ("SPN", "Spanish"), ("FR", "French"),
                        ("CH", "Chinese"), ("ARB", "Arabic"), ("HND", "Hindi"),
                        ("RSN", "Russian"),
                        ("PRT", "Portuguese"), ("JPN", "Japanese"),
                        ("GRM", "German"), ("TUR", "Turkish"),
                        ("VTM", "Vietnamese"), ("THI", "Thai"),
                        ("DCH", "Dutch")]

    BUSINESS_TYPE_CHOICES = [('', 'Select Business Type'), ('MD', 'Media'),
                             ('PRF', 'Professional'),('AFFH','Agriculture, Forestry, Fishing and Hunting'),('MN','Mining'),
                             ('UT','Utilities'),('CNT','Construction'),('MF','Manufacturing'),('WT','Wholesale Trade'),
                             ('RT','Retail Trade'),('TW','Transportation and Warehousing'),('INFO','Information'),
                             ('FI','Finance and Insurance'),('RERL','Real Estate Rental and Leasing'),
                             ('PSTS','Professional, Scientific, and Technical Services'),('MCE','Management of Companies and Enterprises'),
                             ('ASWMRS','Administrative and Support and Waste Management and Remediation Services'),
                             ('ES','Educational Services'),('HCSA','Health Care and Social Assistance'),('AER','Arts, Entertainment, and Recreation'),
                             ('AFS','Accommodation and Food Services'),('OS','Other Services (except Public Administration)'),
                             ('PA','Public Administration')]

    NOTIFICATION_NO = 0
    NOTIFICATION_YES = 1
    NOTIFICATION_CHOICES = [(NOTIFICATION_NO, 'No'), (NOTIFICATION_YES, 'Yes')]

    PROFILE_SECURITY_SEARCH_YES = 1
    PROFILE_SECURITY_SEARCH_NO = 0

    SECURITY_SEARCH_CHOICES = [(PROFILE_SECURITY_SEARCH_NO, 'No'),
                               (PROFILE_SECURITY_SEARCH_YES, 'Yes')]
    #id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    device_type = models.CharField(max_length=10,
                                   choices=DEVICE_TYPE_CHOICES,
                                   blank=True,
                                   default='web')
    phone_num = models.CharField(max_length=12, verbose_name="General User Phone Number", blank=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, verbose_name="Gender",
                                 blank=True, null=True)
    profile_img = models.ImageField(upload_to="skigit/profile/",
                                    verbose_name="Add a personal photo",
                                    blank=True, null=True)
    extra_profile_img = models.ManyToManyField(ExtraProfileImage, blank=True)
    logo_img = models.ManyToManyField(BusinessLogo, blank=True)
    incentive = models.IntegerField(choices=INCENTIVE_CHOICES,
                                    verbose_name="Incentive", blank=True,
                                    null=True)
    skigit_incentive = models.TextField(verbose_name="Skigit Incentive",
                                        blank=True, null=True)
    incetive_val = models.IntegerField('Incentive value($USD)', blank=True,
                                       null=True)
    redemoption_instrucations = models.TextField(
        verbose_name="Redemoption Instrucations", blank=True, null=True)
    coupan_code = models.CharField(max_length=100, verbose_name="Coupan Code",
                                   blank=True, null=True)
    coupan_image = models.ImageField(upload_to="skigit/coupan/",
                                     verbose_name="Add coupan image",
                                     blank=True, null=True)
    contact_name = models.CharField(max_length=100, verbose_name="Contact Name",
                                    blank=True, null=True)
    contact_email = models.EmailField(verbose_name="Contact Email", blank=True,
                                      null=True)
    contact_phone = models.CharField(max_length=12,
                                     verbose_name="Contact Phone", blank=True,
                                     null=True)
    biller_name = models.CharField(max_length=100, verbose_name="Biller Name",
                                   blank=True, null=True)
    biller_address1 = models.CharField(max_length=100,
                                       verbose_name="Biller Address1",
                                       blank=True, null=True)
    biller_address2 = models.CharField(max_length=100,
                                       verbose_name="Biller Address2",
                                       blank=True, null=True)
    payment_method = models.CharField('Payment Type', max_length=1,
                                      choices=PAYMENT_CHOICES, default='0')
    payment_email = models.EmailField(verbose_name="Contact Email for payment",
                                      blank=True, null=True)
    payment_user_name = models.CharField(max_length=35,
                                         verbose_name="Name for payment setup",
                                         blank=True, null=True)
    cover_img = models.OneToOneField(ProfileImg, blank=True, null=True,on_delete=models.CASCADE)
    about_me = models.TextField(verbose_name="About Me", blank=True, null=True)
    birthdate = models.DateField(verbose_name="Date of Birth", blank=True,
                                 null=True)
    language = models.CharField(choices=LANGUAGE_CHOICES, max_length=200,
                                verbose_name="Language", blank=True, null=True)
    country = CountryField(blank_label='Select country', blank=True, null=True)
    state = models.CharField(max_length=30, verbose_name="State", blank=True,
                             null=True)
    city = models.CharField(max_length=30, verbose_name="City", blank=True,
                            null=True)
    zip_code = models.BigIntegerField(verbose_name="Zip Code", blank=True,
                                      null=True)
    # Notification Settings
    like_notify = models.BooleanField('Like Notification', default=True,
                                      blank=False, null=False)
    follow_un_follow_notify = models.BooleanField(
        'Follow/ Un follow Notification', default=True, blank=False, null=False)
    friends_request_notify = models.BooleanField('Friend Request Notification',
                                                 default=True, blank=False,
                                                 null=False)
    friends_accept_notify = models.BooleanField('Friend Accept Notification',
                                                default=True, blank=False,
                                                null=False)
    plug_notify = models.BooleanField('Plug Notification', default=True,
                                      blank=False, null=False)
    un_plug_notify = models.BooleanField('Un Plug Notification', default=True,
                                         blank=False, null=False)
    skigit_notify = models.BooleanField('Skigit Upload Notification',
                                        default=True, blank=False, null=False)
    share_notify = models.BooleanField('Share Skigit Notification',
                                       default=True, blank=False, null=False)
    activation_key = models.CharField(max_length=100, blank=True, null=True)
    key_expires = models.DateTimeField(default=timezone.now)
    company_title = models.CharField(max_length=200,
                                     verbose_name="Company Title", blank=True,
                                     null=True)
    search_profile_security = models.IntegerField(
        choices=SECURITY_SEARCH_CHOICES, verbose_name="Security Search",
        blank=False, default=NOTIFICATION_YES)
    business_type = models.CharField(choices=sorted(BUSINESS_TYPE_CHOICES,key=lambda x: x[1]),
                                     max_length=10,
                                     verbose_name="Business Type", blank=True,
                                     null=True)
    custom_business_type = models.CharField(max_length=10,
                                     verbose_name="Custom Business Type", blank=True,
                                     null=True)

    # Video, Payment, Copyright Management For Staff or Admin User.
    video_management_rights = models.BooleanField('Video Management',
                                                  default=False, blank=True)
    payment_management_rights = models.BooleanField('Payment Management',
                                                    default=False, blank=True)
    copyright_investigation_rights = models.BooleanField('Copyright Management',
                                                         default=False,
                                                         blank=True)
    inappropriate_rights = models.BooleanField('Inappropriate Management',
                                               default=False, blank=True)
    bug_rights = models.BooleanField('Bug Management', default=False,
                                     blank=True)
    email_sent = models.BooleanField('Mail Sent', default=False, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    two_fa_code = models.CharField(null=True, blank=True, max_length=8)
    two_fa_code_expire_at = models.DateTimeField(null=True, blank=True)
    two_fa_by_email = models.BooleanField("Two Factor Verification By Email", default=False)
    two_fa_by_app = models.BooleanField("Two Factor Verification By Mobile App Notification", default=False)
    two_fa_retry = models.IntegerField("Two Factor Code Resend Count", default=0)
    qr_code = models.ImageField(upload_to="skigit/profile/qr/%y/%m/%d", blank=True, null=True)
    ein = models.CharField(verbose_name="Enterprises Identification Number", max_length=10, blank=True, null=True)
    everyone_allowance = models.BooleanField("invitaion allowance for everyone", default=True)
    business_doc = models.ManyToManyField(BusinessDoc, blank=True)
    business_website = models.CharField(max_length=100, verbose_name="Business Website", blank=True, null=True)
    business_verified = models.BooleanField("Verified status", default=False, null=True)
    deactivate_reason = models.CharField(choices=PROFILE_DEACTIVATE_REASON_CHOICES,
                                         max_length=20,
                                         verbose_name="Deactivate Reason",
                                         blank=True,
                                         null=True)
    deactivate_other_reason = models.TextField(verbose_name="Deactivate Other Reason",
                                               blank=True,
                                               null=True)
    #objects = ProfileManager()

    def greet(self):
        return {
            self.GENDER_MALE: 'Hi, boy',
            self.GENDER_FEMALE: 'Hi, girl.'
        }[self.gender]

    def last_seen(self):
        return cache.get('seen_%s' % self.user.username)

    def online(self):
        if self.last_seen():
            now = datetime.now()
            if now > self.last_seen() + timedelta(
                    seconds=settings.USER_ONLINE_TIMEOUT):
                return False
            else:
                return True
        else:
            return False

    @property
    def get_top_profile_img(self):
        if self.profile_img:
            thumbnail = get_thumbnail(self.profile_img, '100x100', crop="center", quality=100)
        else:
            thumbnail = None
        return thumbnail.url if thumbnail else None

    @property
    def is_completed(self):
        status = True
        message = ''
        result = {'status': status, 'message': message}

        fields = [
            self.user.username,
            self.user.first_name,
            self.user.last_name,
            self.user.email,
            self.birthdate,
            self.language,
            self.country,
            self.state,
            self.city,
            self.zip_code
        ]
        is_business = is_user_business(self.user)

        if not all(fields):
            status = False
            message = 'You have not completed all fields or may have entered incorrect information. Please review your entries and error messages for correction. Click SAVE when done.'
        elif is_business and not is_verified_business_user(self.user):
            status = False
            message = 'You can only access your profile page until your account is verified. We will notify you when verified at which time, you will have full access to all Skigit features. Thank you for your patience.'
        elif not self.logo_img.filter(is_deleted=False).all() and is_business:
            status = False
            message = 'You must display at least one logo at all times. Please upload while this popup is displaying, then click OK.'
        elif is_business and self.user.invoice_user and not self.user.invoice_user.filter(type='CreditCard',
                                                                                                is_deleted=False).exists() and not \
                self.user.invoice_user.filter(type='PayPalAccount',
                                                 is_deleted=False).exists():
            status = False
            message = ('Payment information is not verified. Please verify payment method by '
                       'filling PayPal or Credit/Debit card details.')
        elif is_business and self.payment_method == '1' \
                and self.user.invoice_user and not self.user.invoice_user.filter(type='CreditCard',
                                                                                       is_deleted=False).exists():
            status = False
            message = ('Payment information is not verified. Please verify payment method by '
                       'filling PayPal or Credit/Debit card details.')
        elif is_business and self.payment_method == '0' \
                and self.user.invoice_user and not self.user.invoice_user.filter(type='PayPalAccount',
                                                                                       is_deleted=False).exists():
            status = False
            message = ('Payment information is not verified. Please verify payment method by '
                       'filling PayPal or Credit/Debit card details.')
        result.update(status=status, message=message)
        return result

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        # Uncomment this QR profile view 
        super(BaseModel, self).save(*args, **kwargs)
        business_logo_images = self.logo_img.filter(is_deleted=False)
        if is_user_business(self.user) and not self.qr_code and business_logo_images.exists():
            qr = qrcode.QRCode(
                version=5,
                box_size=5,
                border=3
            )
            host = ''.join(settings.HOST)
            sperk_url = "{}/sperk/{}/{}/?code={}".format(host,
                                                         self.user.id,
                                                         business_logo_images.latest('id').id,
                                                         random.choice(QR_SCAN_SECURITY_CODES))
                                                       
            qr.add_data(sperk_url)
            qr.make(fit=True)
            qrcode_img = qr.make_image(fill_color='black', back_color='white')
            canvas = Image.new('RGB', (215, 215), 'white')
            canvas.paste(qrcode_img)
            uuid_value = str(uuid.uuid4())
            file_name = f'{uuid_value}.png'
            buffer = BytesIO()
            canvas.save(buffer, 'PNG')
            self.qr_code.save(file_name, File(buffer), save=True)
            canvas.close()


    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profile"

User.profile = property(lambda u: Profile.objects.get_or_create(user=u)[0])
