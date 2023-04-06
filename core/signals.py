# -*- coding: utf-8 -*-
import logging

from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.db.models.signals import post_delete
from friends.models import FriendInvitation, Friend
from skigit.models import *
from skigit_project.settings import EMAIL_HOST_USER, \
    EMAIL_HOST_REPORT_BUG, EMAIL_HOST_COPYRIGHT
from django.db.models import Q
from django.conf import settings

from mailpost.models import EmailTemplate

logger = logging.getLogger('Signals')


def send_user_created(sender, instance, created, **kwargs):
    """
        At the Time of User Creates Welcome Note send to respected user

    Args:
        sender:
    """
    try:
        if created:

            if FriendInvitation.objects.filter(to_user_email=instance.email).exists():
                for invite_obj in FriendInvitation.objects.filter(to_user_email=instance.email):
                    friend = Friend()
                    friend.to_user = instance
                    friend.from_user = invite_obj.from_user
                    friend.status = "1"
                    FriendInvitation.objects.filter(to_user_email=instance.email).update(status='1', is_member=True)
                    friend.save()

            message = "<table style='width:100%;' cellpadding='0' cellspacing='0'>"\
                    "<tr><td style='text-align:center;'><h3 style='color:#0386B8; margin-bottom:0;'>"\
                    "Welcome To Skigit</h3></td></tr>"\
                    "<tr><td style='text-align:center;'><h5 style='color:#1C913F; margin-top:10px;'>"\
                    "we're so glad you joined us!</h5></td></tr>"\
                    "<tr><td style='text-align:center;'>"\
                    "<a href='http://skigit.com' style='text-decoration:none;color:#0386B8;margin: 20px auto;display: table;'> Login </a></td></tr>"\
                    "<tr><td style='text-align:center;'><img src='http://static.skigit.com/images/shair.png'/ style='width:165px;'></td></tr>"\
                    "</table>"
            subject = "Welcome to Skigit"
            # send_email(subject, message, email, '', EMAIL_HOST_USER)

    except Exception as e:
        msg = e.message


post_save.connect(send_user_created, sender=User)


def send_user_created_email(username, email):
    """
        Social login time mail sending function
    """

    EmailTemplate.send(
        template_key='email_created_social',
        emails=email,
        host=settings.HOST
    )
    

    # try:
    #     message = "<table style='width:100%;' cellpadding='0' cellspacing='0'>"\
    #                 "<tr><td style='text-align:center;'><h3 style='color:#0386B8; margin-bottom:0;font-family: "+"Proza Libre"+", sans-serif;'>"\
    #                 "Welcome To Skigit</h3></td></tr>"\
    #                 "<tr><td style='text-align:center;'><h5 style='color:#1C913F;margin-top:10px;font-family: "+"Proza Libre"+", sans-serif;'>"\
    #                 "we're so glad you joined us!</h5></td></tr>"\
    #                 "<tr><td style='text-align:center;'>"\
    #                 "<a href='http://skigit.com' style='text-decoration:none;color:#0386B8;margin: 20px auto;display: table;font-family: "+"Proza Libre"+", sans-serif;'> Login </a></td></tr>"\
    #                 "<tr><td style='text-align:center;'><img src='https://static.skigit.com/images/shair.png' class='img-responsive' style='width:165px;'/></td></tr>"\
    #                 "</table>"
    #     subject = "Welcome to Skigit"
    #     send_email(subject, message, email, '', EMAIL_HOST_USER)

    # except Exception as e:
    #     msg = e.message


def bug_post_save(sender, instance, created, **kwargs):
    if created:
        try:
            # message = "<table style='width:100%;' cellpadding='0' cellspacing='0'>"\
            #           "<tr><td style='text-align:center;'></tr></td>"\
            #           "<tr><td style='color:#222;'><p style='text-align:justify;'>"\
            #           "<b>Bug Report ID:</b> <a href='http://skigit.com/admin/skigit/bugreport/"+str(instance.id)+"/'>"\
            #           ""+str(instance.id)+"</a><br>"\
            #           "<b>Bug Report Details:</b> "+instance.bug_description+"</p></td></tr>"\
            #           "</table>"
            # subject = "Bug Report"
            # send_email(subject, message, EMAIL_HOST_REPORT_BUG, '', EMAIL_HOST_USER)
            EmailTemplate.send(
                    template_key="bug_report",
                    emails=EMAIL_HOST_REPORT_BUG,
                    context={
                        "id": instance.id,
                        "description": instance.bug_description,
                        "host": ''.join(settings.HOST)[:-1]
                        })
        except Exception as e:
            msg = e.message
post_save.connect(bug_post_save, sender=BugReport)


def copy_post_save(sender, instance, created, **kwargs):

    if created:
        try:
            # CopyRightInvestigation.objects.create(copy_right=instance)

            investigation_id = '%010d' % instance.id
            # message = "<table style='width:100%;' cellpadding='0' cellspacing='0'>"\
            #           "<tr><td style='text-align:center;'>" \
            #           "<h3 style='color:#FF0000; margin-bottom:0;font-family: "+"Proza Libre"+", sans-serif;'>"\
            #           "A Copyright Infringement claim has been submitted!</h3></td></tr>"\
            #           "<tr><td style='color:#222;'><center><p style='text-align:center;'>"\
            #           "<b>Copyright Infringement claim ID:</b>&nbsp;" \
            #           "<a href='http://skigit.com/admin/skigit/copyrightinfringement/"+str(instance.id)+"/'>"\
            #           ""+investigation_id+"</p></center></td></tr></table>"
            # subject = "Copyright Infringement Claim"
            # send_email(subject, message, EMAIL_HOST_COPYRIGHT, '', EMAIL_HOST_USER)
            EmailTemplate.send(
                template_key="copyright_infringement_claim",
                emails=EMAIL_HOST_COPYRIGHT,
                context={
                    "id": instance.id,
                    "investigation_id": investigation_id,
                    "host": ''.join(settings.HOST)[:-1] 
                })
        except Exception as e:
            msg = e # TODO: fix error: e deson't have message func..

        try:
            if VideoDetail.objects.filter(id=instance.skigit_id).exists():
                skigitt = VideoDetail.objects.get(id=instance.skigit_id)
            # message_user = "<table style='width:100%;' cellpadding='0' cellspacing='0'>" \
            #                "<tr><td style='text-align:center;'>" \
            #                "<h4 style='color:#58D68D; margin-bottom:0;font-family: "+"Proza Libre"+", sans-serif;'> " \
            #                "Thank You for Tacking Action!</h4></td></tr>"\
            #                "<tr><td style='color:#222;'><p style='text-align:justify;'>"\
            #                "We are currently investigating your submission regarding&nbsp; " \
            #                "<a href='http://skigit.com/?id="+str(instance.skigit_id)+"' " \
            #                "style='text-decoration:none' ><span style='color:#0386B8;'>" + skigitt.title + "</span></a>." \
            #                "&nbsp;We will contact you as soon as our investigation is" \
            #                " complete.</p><p>Best Regards,<br/>Skigit</p></td></tr>"\
            #                "<tr><td style='text-align:center;width:165px;'>" \
            #                "<img src='https://static.skigit.com/images/shair.png' style='width:165px;'/>" \
            #                "</td></tr></table>"
            # subject = "Thanks for Taking Action!"
            # send_email(subject, message_user, instance.email, '', EMAIL_HOST_COPYRIGHT)
            EmailTemplate.send(
                template_key="thanks_for_taking_action",
                emails=instance.email,
                context={
                    "id": instance.skigit_id,
                    "title": skigitt.title,
                    "host": ''.join(settings.HOST)[:-1]
                })
        except Exception as e:
            msg = e

post_save.connect(copy_post_save, sender=CopyRightInfringement)


def inappropriate_post_save(sender, instance, created, **kwargs):
    if created:
        InappropriateSkigitInvestigator.objects.create(inapp_skigit=instance)
        try:
            if VideoDetail.objects.filter(id=instance.skigit.id).exists():
                skigitt = VideoDetail.objects.get(id=instance.skigit.id)
                # message_user = "<table style='width:100%;' cellpadding='0' cellspacing='0'><tr><td style='text-align:center;'>" \
                #                "<h4 style='color:#58D68D; margin-bottom:0;font-family: "+"Proza Libre"+", sans-serif;'>" \
                #                "Thank You for Tacking Action!</h4></td></tr><tr><td style='color:#222;'>" \
                #                "<p style='text-align:justify;'>We are currently investigating your submission regarding&nbsp;" \
                #                "<a href='http://skigit.com/?id="+str(instance.skigit_id)+"'" \
                #                "style='text-decoration:none'><span style='color:#0386B8;'>" + skigitt.title + \
                #                "</span></a>.</td></tr></table>"
                # subject = "Thanks for Taking Action!"
                # send_email(subject, message_user, instance.reported_user.email, '', EMAIL_HOST_COPYRIGHT)
                EmailTemplate.send(
                    template_key="thanks_for_taking_action",
                    emails=instance.reported_user.email,
                    context={
                        "id": instance.skigit_id,
                        "title": skigitt.title,
                        "host": ''.join(settings.HOST)[:-1]
                })
        except Exception as e:
            msg = e

post_save.connect(inappropriate_post_save, sender=InappropriateSkigit)


def friend_invite_post_save(sender, instance, created, **kwargs):
    """
        Non Skigit Friend Invitations
    """

    if created or ('update_fields' in kwargs and kwargs['update_fields'] and 'updated_date' in kwargs['update_fields']):
        try:
            EmailTemplate.send(
                    template_key="non_skigit_friend_invitation",
                    emails=instance.to_user_email,
                    context={'username': instance.from_user.username, "host": ''.join(settings.HOST)[:-1]})
        except Exception as exc:
            logger.error("Non skigit Friend invitation Failed: ", exc)
            msg = exc

post_save.connect(friend_invite_post_save, sender=FriendInvitation)


def friend_post_save(sender, instance, created, **kwargs):
    """
        Friend Notification Module
        :param sender: User
        :param instance: Friend
        :param created: Boolean Value True or False.... (New Entry in Friends Table returns True otherwise False)
        :param kwargs:
        :return: Returns The Current Notification Count <VALUE STORED IN RADIS CACHE>.
    """

    user = User.objects.get(id=instance.to_user.id)
    if Friend.objects.filter((Q(from_user=user) | Q(to_user=user)), is_read=False).exists():

        f_notification_count = Friend.objects.filter(to_user=user, status=0, is_read=False).count()
        cache.set("count"+str(instance.to_user.id), str(f_notification_count))

post_save.connect(friend_post_save, sender=Friend)


def user_related_delete(sender, instance, **kwargs):
    """

    :param sender:
    :param instance:
    :return: Deletes all user related action/entries...
    """
    if instance.email:
        FriendInvitation.objects.filter(to_user_email__iexact=instance.email).delete()


post_delete.connect(user_related_delete, sender=User)

# social login don't return username for some cases and we need this 
def set_username(sender, instance, **kwargs):
    if not instance.username:
        username = instance.first_name
        counter = 1
        while User.objects.filter(username=username):
            username = instance.first_name + str(counter)
            counter += 1
        instance.username = username

pre_save.connect(set_username, sender=User)