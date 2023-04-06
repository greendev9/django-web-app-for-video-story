from user.models import BusinessLogo, Profile

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import Signal
from django.dispatch.dispatcher import receiver
from django.utils.translation import ugettext as _
from django_countries.fields import CountryField
from sorl.thumbnail import get_thumbnail,delete
from core.api import Api  # temporary
from core.models import BaseModel, Category, SubjectCategory
from sperks.models import Donation, Incentive
from skigit.storage import B2Storage
from skigit.managers import VideoDetailManager, VideoDetailManagerAdmin

from mailpost.models import EmailTemplate


class Video(BaseModel):
    """ Comment: Video Uploading Model
    """

    Public, Unlisted, Private = range(3)

    VIDEO_PERMISSIONS = (
        (Public, "Public"),
        (Unlisted, "Unlisted"),
        (Private, "Private"),
    )

    # below fields provided by django-youtube package
    # ($> pip install django-youtube)
    title = models.CharField(
        max_length=200,
        blank=False,
        db_index=True,
        verbose_name=_("My Skigit Title")
    )
    user = models.ForeignKey(
        User,
        related_name="custom_user_auth1",
        db_index=True,
        on_delete=models.CASCADE
    )
    video_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        help_text=_("The B2 id file from Backblaze")
    )
    filename = models.CharField(
        max_length=44,
        unique=True,
        null=True,
        help_text=_("The B2 name file from Backblaze")
    )
    description = models.TextField(
        null=True,
        blank=True
    )
    youtube_url = models.URLField(
        max_length=255,
        null=True,
        blank=True
    )
    swf_url = models.URLField(
        max_length=255,
        null=True,
        blank=True
    )
    access_control = models.SmallIntegerField(
        choices=VIDEO_PERMISSIONS,
        default=Unlisted
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """ Returns: youtube_url
        """
        if self.youtube_url:
            return self.youtube_url
        else:
            return '{0}{1}'.format(settings.BACKBLAZE_URL, self.filename)
        
    def get_swf_url(self):
        """ Returns: the swf url
        """
        if self.swf_url:
            url = self.swf_url
            if url.lower().startswith('http://'):
                url = url.replace('http://', 'https://', 1).replace('Http://', 'https://', 1).replace('HTTP://', 'https://', 1)
            return url
        else:
            return '{0}{1}'.format(settings.BACKBLAZE_URL, self.filename)
        
    # this works with link only
    def save1(self, *args, **kwargs):
        """ Comment: Synchronize the video information on db with the
        videoLink on Youtube. The reason that I didn't use signals is to
        avoid saving the video instance twice.
        """
        if not self.id:
            super(Video, self).save(*args, **kwargs)
            t = Thumbnail()
            t.filename = "http://img.youtube.com/vi/%s/hqdefault.jpg" % self.video_id
            t.video = self
            t.save()
        else:
            # updating the video instance
            # Connect to API and update video on youtube
            api = Api()

            # update method needs authentication
            api.authenticate()

            # Update the info on youtube, raise error on failure
            api.update_video(self.video_id, self.title, self.description,
                             self.keywords, self.access_control)
        return super(Video, self).save(*args, **kwargs)

    def default_thumbnail(self):
        """ Comment: Returns the 1st thumbnail in thumbnails
                     This method can be updated as adding default attribute the
                     Thumbnail model and return it
            Returns: Thumbnail object
        """
        return self.thumbnails.first() if self.thumbnails.exists() else ''


@receiver(pre_delete, sender=Video)
def delete_video_b2(sender, instance, **kwargs):
    try:    
        b2 = B2Storage()
        b2.delete(instance.video_id, instance.filename)

        original_thumbnail = instance.thumbnails.all()[0].get_absolute_url() # blackblaze image url
        cache_thumbnail = get_thumbnail(original_thumbnail,'x200').url # thumbnail location in media/cache folder
        thumbnail_path = cache_thumbnail.replace('/media/','')
        delete(thumbnail_path) # remove thumbnail from media/cache folder
    except:
        pass


class VideoDetail(BaseModel):
    """ Skigit Management Model.
        Contains full information of Videos uploaded and linked by end user.
    """

    STATUS_CHOICE = (
        (0, 'Pending'),
        (1, 'Publish'),
        (2, 'Reject'),
        (3, 'Delete')
    )

    ACTION_CHOICE = (
        ('0', 'Pending'),
        ('1', 'Appropriate'),
        ('2', 'Inappropriate')
    )

    COPY_ACTION_CHOICE = (
        ('0', 'Open'),
        ('1', 'Under Investigation'),
        ('2', 'Closed'),
        ('3', 'Remove Skigit')
    )
    

    RECEIVE_SPERK = 1
    DONATE_SPERK = 2
    SPERK_CHOICES = (
        (RECEIVE_SPERK, "Receive sperk"),
         (DONATE_SPERK, "Donate sperk")
    )

    IS_LOGO_TRUE = 1
    IS_LOGO_FALSE = 0
    LOGO_CHOICES = (
        (IS_LOGO_TRUE, 'Yes'), (IS_LOGO_FALSE, 'No')
    )

    title = models.CharField(
        max_length=40,
        blank=False,
        verbose_name="My Skigit Title",
        unique=True,
        error_messages={'unique': "This name already exists."}
    )
    category = models.ForeignKey(
        Category,
        default=0,
        on_delete=models.CASCADE
    )
    subject_category = models.ForeignKey(
        SubjectCategory,
        verbose_name=_("My Subject Category"),
        default=0,
        on_delete=models.CASCADE
    )
    made_by = models.ForeignKey(
        User,
        models.SET_NULL,
        limit_choices_to={'groups__name': settings.BUSINESS_USER, 'profile__payment_method__isnull': False,
                          'profile__payment_email__isnull': False},
        verbose_name=_("My awesome thing was made by"),
        help_text=_('Select maker'),
        related_name="video_made_by",
        null=True,
        blank=True,
        
    )
    made_by_option = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("If not found in the list above, add maker or " \
                       "proprietor name"),
        default=''
    )
    bought_at = models.URLField(
        max_length=255,
        null=False,
        blank=False
    )
    add_logo = models.IntegerField(
        choices=LOGO_CHOICES,
        default=IS_LOGO_TRUE
    )
    why_rocks = models.TextField(
        default='',
        max_length=200
    )
    skigit_id = models.ForeignKey(
        Video,
        related_name="videos",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    business_user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="skigit_business_user",
    )
    status = models.IntegerField(
        _('Status'),
        default=0
    )
    is_share = models.BooleanField(
        default=False
    )
    share_skigit = models.ForeignKey(
        Video,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_requests_created",
    )
    inappropriate_skigit = models.CharField(
        _('Inappropriate'),
        max_length=5,
        choices=ACTION_CHOICE,
        blank=True,
        null=True
    )
    is_plugged = models.BooleanField(
        'Plugged',
        default=False
    )
    plugged_skigit = models.ForeignKey(
        Video,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="plugged_skigit",
        verbose_name='Plugged Skigit',
    )
    is_sperk = models.BooleanField(
        _('Sperk'),
        default=False
    )
    receive_donate_sperk = models.IntegerField(
        choices=SPERK_CHOICES,
        verbose_name=_("Sperk choice"),
        default=0
    )
    donate_skigit = models.ForeignKey(
        Donation,
        blank=True,
        null=True,
        verbose_name=_('Donation Organization'),
        related_name="donation_skigit",
        on_delete=models.CASCADE
    )
    incentive = models.ForeignKey(
        Incentive,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    view_count = models.IntegerField(
        blank=True,
        default=0
    )
    is_active = models.BooleanField(
        default=True
    )
    business_logo = models.ForeignKey(
        BusinessLogo,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="associated_business_user",
    )
    copyright_skigit = models.CharField(
        _('Copyright Infringement'),
        max_length=5,
        default=None,
        choices=COPY_ACTION_CHOICE,
        null=True,
        blank=True
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = VideoDetailManager()
    all_objects = VideoDetailManagerAdmin()

    def __str__(self):
        return self.skigit_id.title

    def bought_at_url(self):
        if self.bought_at:
            try:
                brought_url = self.bought_at.split('://')
                if brought_url[1]:
                    return self.bought_at
                else:
                    return 'http://%s' % brought_url[0]
            except:
                return 'http://%s' % self.bought_at

    def save(self, *args, **kwargs):
        if not self.pk:
            # msg = "<p>Your Skigit named <b>%s</b> has been uploaded and is " \
            #       "under review for posting. You'll receive an email and " \
            #       "notification when posted.</p>"
            # msg = msg % self.skigit_id.title
            # subject = _("Your Skigit was Uploaded!")
            # send_email(
            #     subject,
            #     msg,
            #     self.skigit_id.user.email,
            #     '',
            #     settings.EMAIL_HOST_USER)
            try:
                EmailTemplate.send(
                        template_key="your_skigit_was_uploaded",
                        emails=self.skigit_id.user.email,
                        context={"title": self.skigit_id.title}
                    )
            except:
                pass
        super(VideoDetail, self).save(*args, **kwargs)

    def get_profile_img(self):
        """
            Returns: User Profile Image
        """
        return Profile.objects.get(user_id=self.skigit_id.user)

    def get_business_logo(self):
        """ Returns: Business Logo
        """
        return Profile.objects.get(user_id=self.made_by)

    def get_like_status(self):
        """ Returns: Returns Like Status
        """
        status = Like.objects.filter(
            user_id=self.skigit_id.user,
            skigit_id=self.skigit_id,
            status=True
        )
        if status:
            return 'liked'
        else:
            return 'like'

    def get_like_count(self):
        """ Returns: Like Count
        """
        count = Like.objects.filter(
            skigit_id=self.skigit_id,
            status=True
        ).count()

        if count:
            return count
        else:
            return 0

    def get_plug_count(self):
        """ Returns: Plug Count
        """
        count = VideoDetail.objects.filter(
            plugged_skigit=self.skigit_id,
            is_plugged=True, status=True
        ).count()

        if count:
            return count
        else:
            return 0

    class Meta:
        ordering = ('created_date',)
        index_together = (('status', 'is_active'),
                          ('status', 'is_active',
                           'plugged_skigit', 'is_plugged'))

        verbose_name = "Skigit"
        verbose_name_plural = "Skigits"


class Thumbnail(models.Model):
    """ Returns: Thumbnail of video url
    """
    video = models.ForeignKey(
        Video,
        null=True,
        related_name=u"thumbnails",
        db_index=True,
        on_delete=models.CASCADE
    )
    filename = models.URLField(
        max_length=300,
        default=''
    )

    file_id = models.URLField(
        max_length=300,
        default=''
    )

    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        """ Returns: Video Thumbnail Absolute URL's
        """
        if self.file_id:
            return '{0}{1}'.format(settings.BACKBLAZE_URL, self.filename)
        else:
            file_name = self.filename.replace('http://', 'https://')
            return file_name

    def url(self):
        return self.get_absolute_url()

@receiver(pre_delete, sender=Thumbnail)
def delete_thumbnail_b2(sender, instance, **kwargs):
    try:
        b2 = B2Storage()
        b2.delete(instance.file_id, instance.filename)
    except:
        pass


class Favorite(BaseModel):
    skigit = models.ForeignKey(
        Video,
        related_name="favourites",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    status = models.IntegerField(
        default=0
    )
    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        index_together = ('skigit', 'status', 'is_active')
        verbose_name = "Favorite/Unfavorite Skigit"
        verbose_name_plural = "Favorite/Unfavorite Skigits"


class Like(BaseModel):
    """ Comment: Like Skigit Model
    """
    skigit = models.ForeignKey(
        Video,
        related_name="likes",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    status = models.BooleanField(
        blank=False,
        default=True
    )
    is_read = models.BooleanField(
        default=True
    )

    def get_like_status(self):
        if Like.objects.filter(user_id=self.user_id, skigit_id=self.id,
                               status=True).exists():
            return 'liked'
        else:
            return 'like'

    class Meta:
        index_together = ('skigit', 'user', 'status')
        verbose_name = "Like/Unlike Skigit"
        verbose_name_plural = "Like/Unlike Skigits"


class CopyRightInfringement(models.Model):
    INVESTIGATION_STATUS_CHOICES = (
        # (0, 'Open'),
        (1, 'Under investigation'),
        (3, 'Remove Skigit'),
        (2, 'Accept Skigit'),
    )

    REMOVE_ALL_YES = True
    REMOVE_ALL_NO = False
    REMOVE_CHOICES = [(REMOVE_ALL_NO, 'No'), (REMOVE_ALL_YES, 'Yes')]

    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Submitted by User',
        related_name='infringement_copytight_user'
    )
    skigit_id = models.IntegerField(
        'Infringed work on Skigit',
        blank=True,
        null=True
    )
    urls = models.URLField(
        'My Website Urls',
        blank=False,
        null=False
    )
    description = models.TextField(
        'Description',
        blank=False,
        null=False
    )
    address = models.CharField(
        'Street Address',
        max_length=500,
        blank=False,
        null=False
    )
    city = models.CharField(
        'City',
        max_length=100,
        blank=False,
        null=False
    )
    state = models.CharField(
        'State/Province',
        blank=False,
        null=False,
        max_length=200
    )
    zip_code = models.BigIntegerField(
        'Zip/Postal Code',
        blank=True,
        null=True
    )
    country = CountryField(
        blank_label='Country',
        blank=False,
        null=False
    )
    phone = models.CharField(
        'Phone Number',
        max_length=200,
        blank=False,
        null=False
    )
    email = models.EmailField(
        'Email Address',
        max_length=200,
        blank=False,
        null=False
    )
    submitter_request = models.BooleanField(
        'Submitter Request Remove all',
        default=None,
        blank=False,
        choices=REMOVE_CHOICES
    )
    full_name = models.CharField(
        'Full name',
        max_length=500,
        blank=False,
        null=False
    )
    complaint_date = models.DateField(
        'Complaint Date',
        auto_created=True,
        auto_now=True,
        editable=False
    )
    submitted_by = models.ForeignKey(
        Profile,
        blank=False,
        null=False,
        related_name='complaint_by_register_user',
        verbose_name='Submitted by',
        on_delete=models.CASCADE
    )
    signature = models.CharField(
        'Electronic Signature',
        max_length=200,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        'Investigation Status',
        default=0,
        choices=INVESTIGATION_STATUS_CHOICES,
        blank=True,
        null=True
    )
    created_date = models.DateTimeField(
        'Report created date',
        auto_created=True,
        auto_now_add=True,
        editable=False
    )
    updated_date = models.DateTimeField(
        'Report updated date',
        auto_created=True,
        auto_now=True
    )

    def __str__(self):
        return self.user_id.get_full_name()

    class Meta:
        verbose_name = "Copyright Infringement"
        verbose_name_plural = "Copyright Infringement"


class CopyRightInvestigation(models.Model):
    REMOVE_ALL_YES = True
    REMOVE_ALL_NO = False
    REMOVE_CHOICES = [(REMOVE_ALL_NO, 'No'), (REMOVE_ALL_YES, 'Yes')]

    copy_right = models.ForeignKey(
        CopyRightInfringement,
        blank=True,
        null=True,
        verbose_name='Copy Right Infringement',
        on_delete=models.CASCADE
    )
    investigator_name = models.ForeignKey(
        Profile,
        blank=True,
        null=True,
        related_name='user_investigator_name',
        verbose_name='Investigator Name',
        on_delete=models.CASCADE
    )
    remove_all = models.BooleanField(
        'Remove all',
        default=REMOVE_ALL_NO,
        blank=False,
        choices=REMOVE_CHOICES
    )
    strike = models.BooleanField(
        'Strike',
        default=REMOVE_ALL_NO,
        blank=False,
        choices=REMOVE_CHOICES
    )
    description = models.TextField(
        'Investigation Description and conclusion',
        blank=True,
        null=True
    )
    action = models.TextField(
        'Action Taken',
        blank=True,
        null=True
    )
    created_date = models.DateTimeField(
        'Investigation created date',
        auto_created=True,
        auto_now_add=True,
        editable=False
    )
    updated_date = models.DateTimeField(
        'Investigation updated date',
        auto_created=True,
        auto_now=True
    )

    class Meta:
        verbose_name = "Copyright Investigation"
        verbose_name_plural = "Copyright Investigation"


class UploadedVideo(models.Model):
    """ Comment: Temporary video object that is uploaded to use in direct upload
    """

    file_on_server = models.FileField(
        upload_to='videos/temp', null=True,
        help_text=_("Temporary file on server for using in `direct upload` "
                    "from your server to youtube")
    )

    def __str__(self):
        """string representation"""
        return self.file_on_server.url


class UploadedVideoLink(models.Model):
    """ temporary video object that is uploaded to use in direct upload
    """

    video_link = models.TextField(null=True)

    def __str__(self):
        """string representation"""
        return self.video_link


video_created = Signal(providing_args=["video"])


class InappropriateSkigitReason(BaseModel):
    class Meta:
        verbose_name = _("Inappropriate skigit Reason")
        verbose_name_plural = _("Inappropriate Skigit Reasons")

    reason_title = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Reason Title",
        blank=False
    )
    reason_slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_("Reason Slug"),
        blank=False)

    def __str__(self):
        return self.reason_title


class InappropriateSkigit(BaseModel):
    class Meta:
        verbose_name = _("Inappropriate Skigit")
        verbose_name_plural = _("Inappropriate Skigits")

    STATUS_CHOICE = (
        ("2", 'Under Investigation'),
        ("4", 'Remove Skigit'),
        ("3", 'Accept Skigit'),
    )

    ACTION_CHOICE = (
        ('0', 'Pending'),
        ('1', 'Appropriate'),
        ('2', 'Inappropriate')
    )

    skigit = models.ForeignKey(
        VideoDetail,
        verbose_name="Skigit",
        related_name="Skigit",
        on_delete=models.CASCADE
    )
    reported_user = models.ForeignKey(
        User,
        verbose_name=_('Reported User'),
        related_name='Reported_User',
        on_delete=models.CASCADE
    )
    reason = models.ForeignKey(
        InappropriateSkigitReason,
        verbose_name=_('Inappropriate Reason'),
        related_name='Inappropriate_Skigit_Reason',
        on_delete=models.CASCADE
    )
    action = models.CharField(
        _('Action'),
        max_length=20,
        choices=ACTION_CHOICE,
        default='0'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICE,
        default="2",
        verbose_name=_("Status")
    )

    def __str__(self):
        return self.skigit.title

    def save(self, *args, **kwargs):
        if not self.pk:
            message = "Thank You %s To Notify Skigit Team %s As %s " % (
                self.reported_user.username,
                self.skigit.skigit_id.title,
                self.reason.reason_title)
            subject = "Inappropriate | Skigit"
            video = VideoDetail.objects.get(pk=self.skigit.id)
            video.inappropriate_skigit = 0
            video.save()
            # send_mail(subject, message, settings.EMAIL_HOST_USER,
            # [self.reported_user.email, ])
        super(InappropriateSkigit, self).save(*args, **kwargs)


class InappropriateSkigitInvestigator(BaseModel):
    REMOVE_ALL_YES = True
    REMOVE_ALL_NO = False
    REMOVE_CHOICES = [(REMOVE_ALL_NO, 'No'), (REMOVE_ALL_YES, 'Yes')]
    inapp_skigit = models.ForeignKey(
        InappropriateSkigit,
        related_name="inappskigit",
        verbose_name="Inappropriate Skigit",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    investigating_user = models.ForeignKey(
        User,
        models.SET_NULL,
        verbose_name="Investigating User",
        related_name="Investigating_User",
        blank=True,
        null=True,
    )
    result_remove_all = models.BooleanField(
        default=REMOVE_ALL_NO,
        blank=False,
        choices=REMOVE_CHOICES
    )
    result_strike = models.BooleanField(
        default=REMOVE_ALL_NO,
        blank=False,
        choices=REMOVE_CHOICES
    )
    investigation_discription = models.TextField(
        'Investigation Description and conclusion',
        blank=True,
        null=True
    )
    action_taken = models.TextField(
        'Action Taken',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Inappropriate skigit Investigator"
        verbose_name_plural = "Inappropriate skigit Investigator"


class Payment(models.Model):
    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True
    )
    payment_email = models.EmailField(
        'Account Email ID',
        blank=True,
        null=True
    )
    payment_name = models.CharField(
        'Account Holder Name',
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.payment_name

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payment"


# Model For Bug Report
class BugReport(models.Model):
    BUG_STATUS_CHOICES = (
        (0, 'Open'),
        (1, 'Under investigation'),
        (2, 'Closed'),
    )

    user = models.CharField(
        'User',
        max_length=300,
        blank=True,
        null=True
    )
    skigit_id = models.ForeignKey(
        VideoDetail,
        blank=True,
        null=True,
        related_name='bug_report_skigit',
        verbose_name="Skigit",
        on_delete=models.CASCADE
    )
    bug_title = models.CharField(
        'Title',
        max_length=300,
        blank=True,
        null=True
    )
    bug_page_url = models.URLField(
        'URL',
        blank=True,
        null=True
    )
    bug_description = models.TextField(
        'Description',
        blank=True,
        null=True
    )
    bug_comment = models.TextField(
        'Comments',
        blank=True,
        null=True
    )
    bug_status = models.IntegerField(
        'Status',
        default=0,
        choices=BUG_STATUS_CHOICES,
        null=True,
        blank=True
    )
    bug_repeated = models.BooleanField(
        'Bug repeated',
        default=False,
        blank=True
    )
    bug_repeated_count = models.IntegerField(
        'Bug repeated count',
        default=0,
        blank=True,
        null=True
    )
    created_date = models.DateTimeField(
        'Report created date',
        auto_created=True,
        auto_now_add=True,
        editable=False
    )
    updated_date = models.DateTimeField(
        'Report updated date',
        auto_created=True,
        auto_now=True
    )

    def __str__(self):
        if self.bug_title:
            return self.bug_title
        else:
            return ""

    class Meta:
        verbose_name = "Bug Report Management"
        verbose_name_plural = "Bug Report Management"
