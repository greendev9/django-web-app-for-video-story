from django.db import models
from django.utils.translation import ugettext as _
import datetime
from core.models import BaseModel
from django.contrib.auth.models import User


class Donation(BaseModel):
    """ Comment: Donation Model
    """

    ngo_name = models.CharField(
        _('Organization Name'),
        max_length=200
    )
    url = models.URLField(
        'URL'
    )
    ngo_description = models.TextField(
        _('About'),
        blank=True,
        null=True
    )

    def __str__(self):
        return self.ngo_name

    class Meta(object):
        verbose_name = _('Donation')
        verbose_name_plural = _('Donation')
        ordering = ['ngo_name']


class Incentive(BaseModel):
    """ Comment: Incentive Model
    """
    title = models.CharField(
        max_length=200,
        blank=False,
        verbose_name=_("Incentive Title")
    )
    amount = models.DecimalField(
        'Amount($)',
        max_digits=9,
        decimal_places=2,
        blank=True,
        default=0.00
    )
    is_paid = models.BooleanField(
        'Amount Paid',
        default=False
    )
    billing_month = models.DateField(
        auto_created=True,
        editable=False,
        default=datetime.date.today
    )
    RECEIVE_SPERK = 1
    DONATE_SPERK = 2
    SPERK_CHOICES = (
        (RECEIVE_SPERK, "Receive sperk"),
         (DONATE_SPERK, "Donate sperk")
    )
    sperk_type = models.IntegerField(
        choices=SPERK_CHOICES,
        null=True
    )
    user = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.title
