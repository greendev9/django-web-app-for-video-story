from django.core.mail import send_mail, EmailMultiAlternatives
from celery import shared_task
from django.conf import settings

@shared_task
def send_async_emails(emails, subject=None, body=None, sender=None,
                      alternatives=None, bcc=None, attachments=None):
    msg = EmailMultiAlternatives(subject, body, sender, emails,
                                 alternatives=((body, 'text/html'),), # DON'T REMOVE COMMA!
                                 bcc=bcc)
    if attachments:
        for name, content, mimetype in attachments:
            msg.attach(name, content, mimetype)

    msg.send(fail_silently=not settings.DEBUG)
