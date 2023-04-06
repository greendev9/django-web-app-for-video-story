from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from core.models import BaseModel
from skigit.models import Video, VideoDetail


class Share(BaseModel):
    skigit_id = models.ForeignKey(
        VideoDetail,
        related_name='shared_video_id',
        verbose_name='Skigit id',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='share_from_user',
        verbose_name=_('From User'),
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='share_to_user',
        verbose_name='To User',
        on_delete=models.CASCADE
    )
    social_site = models.CharField(
        max_length=200,
        blank=False
    )
    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        index_together = (('skigit_id', 'user', 'to_user', 'is_active'),)
        verbose_name = "Share Skigit"
        verbose_name_plural = "Share Skigits"


class Follow(BaseModel):
    # following (me) # current user id
    user = models.ForeignKey(
        User,
        related_name="following_user",
        on_delete=models.CASCADE
    )
    # follower user id # skigit creator id
    follow = models.ForeignKey(
        User,
        related_name="follower_user",
        on_delete=models.CASCADE
    )
    status = models.BooleanField(
        blank=False,
        default=True
    )
    is_read = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = _("Follow/Unfollow Skigit")
        verbose_name_plural = _("Follow/Unfollow Skigits")


class Plugged(BaseModel):
    skigit = models.ForeignKey(Video,on_delete=models.CASCADE)
    # who Plugged user id
    user = models.ForeignKey(
        User,
        related_name="plugging_user",
        on_delete=models.CASCADE
    )
    # From Which  user
    plugged = models.ForeignKey(
        User,
        related_name="from_plugged",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        index_together = ('skigit', 'user', 'plugged')
        verbose_name = _("Favorite/Unfavorite Skigit")
        verbose_name_plural = _("Favorite/Unfavorite Skigits")
