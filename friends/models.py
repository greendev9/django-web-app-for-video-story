from django.contrib.auth.models import User
from django.db import models

from core.models import BaseModel
from skigit.models import Video
from user.models import BusinessLogo


class InviteMessage(BaseModel):
    """
        Friend Invitation Message Model
    """
    invite_message = models.TextField(
        'Invite Message',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Friends Invitation Message"
        verbose_name_plural = "Friends Invitation Message"


class FriendInvitation(BaseModel):
    """ External And Internal Friend Invitation Model
    """

    ACTION_CHOICE = {
        ('0', 'Pending'),
        ('1', 'Friends'),
    }

    to_user_email = models.EmailField("Email")
    invite_text = models.ForeignKey(
        InviteMessage,
        blank=True,
        null=True,
        verbose_name='Invite Message',
        on_delete=models.CASCADE
    )
    is_member = models.BooleanField(
        "Is Skigit Member",
        default=False
    )
    from_user = models.ForeignKey(
        User,
        related_name="UserInvitation",
        verbose_name="Invited by User",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    status = models.CharField(
        'Status',
        max_length=5,
        choices=ACTION_CHOICE,
        default='0'
    )
    invited_date = models.DateField(
        'Invitation Date',
        auto_created=True,
        auto_now_add=True,
        editable=False
    )

    def __str__(self):
        return self.to_user_email

    class Meta:
        verbose_name = "Friends Invite"
        verbose_name_plural = "Friends Invite"


class Friend(BaseModel):
    """ Friend Model
    """

    ACTION_CHOICE = {
        ('0', 'Pending'),
        ('1', 'Friends'),
        ('2', 'Remove friend'),
        ('3', 'Not a Friends'),
    }

    from_user = models.ForeignKey(
        User,
        verbose_name='From User',
        related_name='from_user',
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User,
        verbose_name='To User',
        related_name='to_user',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        'Status',
        max_length=5,
        choices=ACTION_CHOICE,
        default='0'
    )
    is_active = models.BooleanField(
        default=True
    )
    is_read = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.from_user.username

    class Meta:
        index_together = (('from_user', 'status', 'is_active'),
                          ('to_user', 'status', 'is_active'))
        verbose_name = "Friend"
        verbose_name_plural = "Friends"


class SocialShareThumbnail(BaseModel):
    """
        Social Share Thumbnail Model
    """

    video = models.ForeignKey(
        Video,
        null=True,
        related_name=u"social_share_thumbnails",
        on_delete=models.CASCADE
    )
    url = models.URLField(
        max_length=555
    )
    business_logo = models.ForeignKey(
        BusinessLogo,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="Business_Logo"
    )

    def __str__(self):
        return self.url


class Notification(BaseModel):
    """ Notification Model
    """
    message = models.TextField(
        'Message',
        blank=True,
        null=True
    )
    skigit = models.ForeignKey(
        Video,
        blank=True,
        null=True,
        on_delete = models.CASCADE
    )
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    from_user = models.ForeignKey(
        User,
        related_name='NotificationSenderUser',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    msg_type = models.CharField(
        'Message Type',
        db_index=True,
        max_length=30,
        blank=True,
        null=True
    )
    is_read = models.BooleanField(
        'Read by User',
        default=False
    )
    is_view = models.BooleanField(
        'Viewed by User',
        default=False
    )
    is_active = models.BooleanField(
        'Deleted by User',
        default=True
    )

    class Meta:
        index_together = (('skigit', 'user', 'from_user', 'is_view', 'is_active'), )
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"


class Embed(BaseModel):
    """ Embed Skigit Model
    """

    EMBED_TYPE = {
        ('0', 'Internal'),
        ('1', 'External')
    }

    from_user = models.ForeignKey(
        User,
        verbose_name='From User',
        related_name='embed_from_user',
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User,
        verbose_name='To User',
        related_name='embed_to_user',
        on_delete=models.CASCADE
    )
    skigit_id = models.ForeignKey(
        Video,
        verbose_name='Skigit',
        related_name='embed_video_id',
        on_delete=models.CASCADE
    )
    is_embed = models.BooleanField(
        default=True
    )
    embed_count = models.IntegerField(
        'Embed Count',
        default=0
    )
    embed_type = models.CharField(
        'Embed Type',
        max_length=5,
        choices=EMBED_TYPE,
        default='0'
    )

    class Meta:
        index_together = (('from_user', 'embed_type', 'is_embed'),
                          ('to_user', 'embed_type', 'is_embed'))
        verbose_name = "Embed"
        verbose_name_plural = "Embed"


class WallPoster(BaseModel):
    """
        Skigit Store Wall Poster
    """

    skigit_logo = models.ImageField(
        'Skigit Logo',
        upload_to='media/skigit/brochure/',
        blank=True,
        null=True
    )
    poster_1 = models.ImageField(
        'Wall Poster 18"x24"',
        upload_to='media/skigit/brochure/',
        blank=True,
        null=True
    )
    poster_2 = models.ImageField(
        'Wall Poster 24"x36"',
        upload_to='media/skigit/brochure/',
        blank=True, null=True)
    header_image = models.ImageField(
        upload_to='media/skigit/brochure',
        blank=True,
        null=True
    )
    header_text = models.CharField(
        'Header Text',
        max_length=300,
        blank=True,
        null=True
    )
    content1 = models.TextField(
        'Content 1',
        blank=True,
        null=True
    )
    content2 = models.TextField(
        'Content 2',
        blank=True,
        null=True
    )
    content3 = models.TextField(
        'Content 3',
        blank=True,
        null=True)
    content4 = models.CharField(
        'Skigit URL',
        max_length=500,
        blank=True,
        null=True
    )
    footer_text = models.TextField(
        'Footer Text',
        max_length=500,
        blank=True,
        null=True
    )

    def __str__(self):
        """string representation"""
        return self.header_text

    class Meta:
        verbose_name = "Store Wall Poster"
        verbose_name_plural = "Store Wall Poster"


class PosterBusinessLogo(BaseModel):
    """ Skigit Poster Business Logo By User
    """
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        verbose_name='Business User',
        on_delete=models.CASCADE
    )
    wall_post = models.ForeignKey(
        WallPoster,
        blank=True,
        null=True,
        verbose_name='Wall Poster',
        on_delete=models.CASCADE
    )
    b_logo = models.URLField(
        'Business Logo',
        blank=True,
        null=True
    )

    poster_img = models.ImageField('poster_img', upload_to='media/skigit/brochure/users/', blank=True, null=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Wall Poster Business Logo"
        verbose_name_plural = "Wall Poster Business Logo"


class Brochure(BaseModel):
    """ Skigit Brochure Poster
    """
    header_text = models.CharField('Header Text', max_length=300, blank=True, null=True)
    poster_1 = models.ImageField('Brochure', upload_to='media/skigit/brochure/', blank=True, null=True)

    def __str__(self):
        return self.header_text

    class Meta:
        verbose_name = "Brochure"
        verbose_name_plural = "Brochure"


class BrochureBLogo(BaseModel):
    """ Skigit Poster Business Logo By User
    """
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        verbose_name='Business User',
        on_delete=models.CASCADE
    )
    brochure = models.ForeignKey(
        Brochure,
        blank=True,
        null=True,
        verbose_name='Brochure',
        on_delete=models.CASCADE
    )
    b_logo = models.URLField(
        'Business Logo',
        blank=True,
        null=True
    )

    poster_img = models.ImageField('poster_img', upload_to='media/skigit/brochure/users/', blank=True, null=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Brochure Business Logo"
        verbose_name_plural = "Brochure Business Logo"
