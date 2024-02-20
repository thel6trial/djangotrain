import os
from celery import Celery
from django.apps import apps
import blog.tasks
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangotraining.settings")

app = Celery('djangotraining', broker='redis://djangotraining-redis-1:6379/0', include=['blog.tasks'])

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send_hourly_notification_email': {
        'task': 'send_hourly_notification_email',
        'schedule': 3600.0,  
    },
}