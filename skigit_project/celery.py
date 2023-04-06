from __future__ import absolute_import, unicode_literals
from celery import Celery
import os

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skigit_project.settings')

REDIS_BROKER_URL = settings.CONSTANCE_REDIS_CONNECTION
#AMQP_BROKER_URL = 'amqp://localhost//'
app = Celery('skigit_project', broker=REDIS_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
