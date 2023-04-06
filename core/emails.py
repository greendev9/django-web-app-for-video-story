# -*- coding: utf-8 -*-
from django.core.mail import EmailMultiAlternatives, get_connection
from skigit_project import settings

from mailpost.models import EmailTemplate


def mail_send(email_subject, email_body, email_to, email_from):
    """
       HTML Template Mail Sending Function
    """

    try:
        connection = get_connection(
            username=email_from,
            password=settings.EMAIL_HOST_PASSWORD,
            fail_silently=False)
        email = EmailMultiAlternatives(email_subject, email_body, email_from, [email_to], '')
        email.attach_alternative(email_body, "text/html")
        email.send()

    except Exception as e:
        #email = e.message
        print(e)


def send_email(email_subject, mail_body, to_email, header_body, from_email):

    email_body ='<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' \
                '<html xmlns="http://www.w3.org/1999/xhtml">' \
                '<head>' \
                '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />' \
                '<title>Email | Skigit</title>' \
                '<link href="https://fonts.googleapis.com/css?family=Proza+Libre:400i" rel="stylesheet" type="text/css"/>'\
                '</head>' \
                '<body style="margin:0;">' \
                '<table style="width:100%;" cellpadding="0" cellspacing="0">' \
                '<tr>' \
                '<td>' \
                '<table style="width:400px; margin:10px auto" cellpadding="0" cellspacing="0">' \
                '<tr>' \
                '<td style="width:100%;">' \
                '<table style="width:100%;" cellpadding="0" cellspacing="0">' \
                '<tr valign="top">' \
                '<td tyle="width:100%;">' \
                '<img src="https://static.skigit.com/skigit/images/logo.png" style="margin:0 auto; width:70px; display:table"/>' \
                '</td>' \
                '</tr>' \
                '</table>' \
                '<link href="https://fonts.googleapis.com/css?family=Proza+Libre:400i" rel="stylesheet" type="text/css"/>'\
                ''+mail_body+'' \
                '</td>' \
                '</tr>' \
                '</table>' \
                '</td>' \
                '</tr>' \
                '</table>' \
                '</body>' \
                '</html>' \

    subject = email_subject
    email_to = to_email
    email_from = from_email
    mail_send(subject, email_body, email_to, email_from)


def coupan_email(subject, to_email, from_email, html_body):

    email_body = "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>" \
                 "<html xmlns='http://www.w3.org/1999/xhtml'>" \
                 "<head>" \
                 "<meta http-equiv='Content-Type' content='text/html; charset='utf-8' />" \
                 "<title>Email | Skigit </title>" \
                 "<link href='https://fonts.googleapis.com/css?family=Proza+Libre:400i' rel='stylesheet'>"\
                 "</head>" \
                 "<body style='margin:0;'>" \
                 "<link href='https://fonts.googleapis.com/css?family=Proza+Libre:400i' rel='stylesheet' type='text/css'/>"\
                 "<table style='width:100%;' cellpadding='0' cellspacing='0'>" \
                 "<tr>" \
                 "<td>" \
                 "<link href='https://fonts.googleapis.com/css?family=Proza+Libre:400i' rel='stylesheet'>"\
                 "<table style='width:630px; margin:10px auto;' cellpadding='0' cellspacing='0'>" \
                 "<tr>" \
                 "<td style='width:100%;'>" \
                 "<table style='width:100%;' cellpadding='0' cellspacing='0'>" \
                 "<tr valign='top'>" \
                 "<td tyle='width:100%;'>" \
                 "<img src='https://static.skigit.com/skigit/images/logo.png' style='margin:0 auto; width:70px; display:table;'/>" \
                 "</td>" \
                 "</tr>" \
                 "</table>" \
                 "<link href='https://fonts.googleapis.com/css?family=Proza+Libre:400i' rel='stylesheet' type='text/css'/>"\
                 ""+html_body+""\
                 "</td>" \
                 "</tr>" \
                 "</table>" \
                 "</td>" \
                 "</tr>" \
                 "</table>" \
                 "</body>" \
                 "</html>"

    mail_send(subject, email_body, to_email, from_email)


def custom_email(subject, email_to, mail_body, from_email):

    email_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' \
                 '<html xmlns="http://www.w3.org/1999/xhtml">' \
                 '<head>' \
                 '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />' \
                 '<meta name="viewport" content="width=device-width, initial-scale=1"/>' \
                 '<title>Coupan|Skigit</title>' \
                 '<link href="https://fonts.googleapis.com/css?family=Montserrat" rel="styleshee" type="text/css"/>' \
                 '<link href="https://static.skigit.com/skigit/css/segio_font.css" rel="stylesheet" type="text/css"/>' \
                 '</head>' \
                 '<body>' \
                 '<table style="width:100%;" cellpadding="0" cellspacing="0">' \
                 '<tr>' \
                 '<td>' \
                 '<table cellpadding="0" cellspacing="0" style="max-width:680px; margin:0 auto;">' \
                 '<tr>' \
                 '<td>' \
                 '<table cellpadding="0" cellspacing="0" style="width:100%">' \
                 '<tr>' \
                 '<td>' \
                 '<img src="https://static.skigit.com/skigit/images/logo.png" style="width:70px"/>' \
                 '</td>' \
                 '</tr>' \
                 '</table>' \
                 '<table cellpadding="0" cellspacing="0" style="width:100%">' \
                 '<tr>' \
                 '<td>' \
                 '<table cellpadding="0" cellspacing="0" style="width:100%; color: gray">' \
                 '<tr>' \
                 '<td style="width:37px">' \
                 '</td>' \
                 '<td>' \
                 '<table cellpadding="0" cellspacing="0" style="width:100%; font-size:20px; padding-right: 10px;">' \
                 '<tr>' \
                 '<td style="width:100%; height:10px;">' \
                 '</td>' \
                 '</tr>' \
                 '<tr>' \
                 '<td style="margin:0; text-align:center; color:#58D68D; font-family: segoe_print !important; font-style: italic;" >' \
                 '<center><strong><h4 style="margin:0"><img src="https://static.skigit.com/skigit/images/newpost.png" style="width:30px"/>' \
                 '<span style="font-family: Segoe_Print !important;  color:#58D68D;">Congratulations! Skigit would like to command you on your awesomeness!' \
                 '</sapn></h4></strong></center>' \
                 '</td>' \
                 '</tr>' \
                 '<tr>' \
                 '<td style="width:100%; height:20px;">' \
                 '</td>' \
                 '</tr>' \
                 '<tr>' \
                 + mail_body + \
                 '<td style="width:100%; height:10px;">&nbsp;' \
                 '</td>' \
                 '</tr>' \
                 '<tr>' \
                 '<td style="width:100%; font-size:14px; color: #1599dc;  font-family: segoe_print !important;font-style: italic; text-align:center">' \
                 '<span>' \
                 'Share your skigits with family, friends... the whole world!' \
                 '</span>' \
                 '</td>' \
                 '</tr>' \
                 '</table>' \
                 '</td>' \
                 '</tr>' \
                 '</table>' \
                 '</td>' \
                 '</tr>' \
                 '</table>' \
                 '</body>' \
                 '</html>'

    mail_send(subject, email_body, email_to, from_email)
