from django.test import TestCase
from django.core.mail import get_connection

from skigit_project import settings

from mailpost.models import (EmailHost, EmailHeader,
                             EmailFooter, EmailTemplate)
# Create your tests here


class MailPostFunctionalityTestCase(TestCase):
    """ 
    Tests for checking email and template
    functionality of mailpost app.
    """

    def setUp(self):
        host = EmailHost.objects.create(
            name="HOST",
            email="accounts@skigit.com"
        )
        
        header_html = "<!DOCTYPE html><html><body>"
        body_html = "<h1>Hello {{name}}</h1>"
        footer_html = "</body></html>"

        header = EmailHeader.objects.create(
            html_template = header_html,
            template_key="test_header"
        )
        footer = EmailFooter.objects.create(
            html_template=footer_html,
            template_key="test_footer"
        )
        template = EmailTemplate.objects.create(
            template_name = "Test Template",
            subject = "Test Subject",
            from_email=host,
            html_template=body_html,
            header=header,
            footer=footer,
            template_key="test_template"
        )

    def test_template_was_created(self):
        template = EmailTemplate.objects.get(template_key="test_template")
        self.assertIsInstance(template, EmailTemplate)
    
    def test_mail_was_sent(self):
        success = False
        try:
            EmailTemplate.send("test_tempate", "bug@skigit_com")
            success = True
        except:
            pass
        self.asserTrue(success)