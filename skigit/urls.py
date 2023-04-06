
from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^remove-profile-pic/?$', ajax_remove_images, name="remove_profile_pic"),
]
