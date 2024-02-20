from celery import app as celery_app
from blog.tasks import (
    send_notification_email,
    send_hourly_notification_email,
)

__all__ = ('celery_app',)