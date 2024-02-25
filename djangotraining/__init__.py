from celery import app as celery_app
import pymysql

pymysql.install_as_MySQLdb()
from blog.tasks import (
    send_notification_email,
    send_hourly_notification_email,
)

__all__ = ('celery_app',)