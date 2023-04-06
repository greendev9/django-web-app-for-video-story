from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from django.shortcuts import render
from allauth.exceptions import ImmediateHttpResponse

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin): 
        user = sociallogin.user
        if user.id:  
            return          
        try:
            if user.email and user.email != '' and user.email is not None:
                authuser = User.objects.filter(email__iexact=user.email.strip())  # if user exists, connect the account to the existing account and login
                if authuser.exists():
                    message = 'Your email address  ' + user.email + '  is already registered with Skigit.com. Please Sign in with that email.'
                    raise ImmediateHttpResponse(render(request, 'socialaccount/login_error.html', {'type': True, 'message': message}))                  
        except User.DoesNotExist:
            pass

        