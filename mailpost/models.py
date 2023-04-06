from django import template
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db import models
from django.template import Context

from core.tasks import send_async_emails


class EmailHost(models.Model):
    """ EmailHost used as from_email in sending emails """
    host_name = models.CharField(max_length=255, unique=True)
    email = models.CharField(max_length=255, unique=False )
    description = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s <%s>" % (self.host_name, self.email)


class EmailHeader(models.Model):
    """ Email template header used to generate main template """
    html_template = models.TextField(blank=True, null=True)
    # unique identifier of the email template
    template_key = models.CharField(max_length=255, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s" % self.template_key 


class EmailFooter(models.Model):
    """ Email template footer used to generate main template """
    html_template = models.TextField(blank=True, null=True)
    # unique identifier of the email template
    template_key = models.CharField(max_length=255, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s" % self.template_key


class EmailTemplate(models.Model):
    """
    Email templates get stored in database so that admins can
    change emails on the fly
    """
    template_name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    from_email = models.ForeignKey(EmailHost,on_delete=models.CASCADE)
    html_template = models.TextField()
    header = models.ForeignKey(EmailHeader,on_delete=models.CASCADE)
    footer = models.ForeignKey(EmailFooter,on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    # unique identifier of the email template
    template_key = models.CharField(max_length=255, unique=True)

    def get_rendered_template(self, tpl, context):
        return self.get_template(tpl).render(context)

    def get_template(self, tpl):
        return template.Template(tpl)

    def get_subject(self, subject, context):
        return subject or self.get_rendered_template(self.subject, context)

    def get_body(self, context):
        header = self.header.html_template
        footer = self.footer.html_template
        body = self.html_template
        html = header + body + footer
        return self.get_rendered_template(html, context)

    def get_sender(self):
        return self.from_email.email or settings.DEFAULT_FROM_EMAIL

    def get_recipient(self, emails):
        if type(emails) == str:
            return [emails]
        else:
            return emails

    @staticmethod
    def send(*args, **kwargs):
        """ Main function used for sending emails.

        Main Params:
            template_key: string
            emails: string/list
            context: dict - for changing values in email template
            attachments: file object
            *kwargs: see class for more info

        """
        EmailTemplate._send(*args, **kwargs)

    @staticmethod
    def _send(template_key, emails, context=None, subject=None, body=None, sender=None,
              bcc=None, attachments=None):
        mail_template = EmailTemplate.objects.get(template_key=template_key)
        context = Context(context)

        emails = mail_template.get_recipient(emails)
        subject = mail_template.get_subject(subject, context)
        body = mail_template.get_body(context)
        sender = sender or mail_template.get_sender()
        
        send_async_emails.delay(emails, subject, body, sender,
                                alternatives=((body, 'text/html'),), # DON'T REMOVE COMMA!
                                bcc=bcc,
                                attachments=attachments)

    def __str__(self):
        return "<{}> {}".format(self.template_key, self.subject)
