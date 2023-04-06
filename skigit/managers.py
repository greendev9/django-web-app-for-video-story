'''
All skigit app managers here!
'''
from django.db import models

class VideoDetailManager(models.Manager):
    '''
    Show skigits only having is_active
    '''

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class VideoDetailManagerAdmin(models.Manager):
    '''
    Show all skigits in admin end
    '''

    def get_queryset(self):
        return super().get_queryset()
