from djangotraining.celery import Celery
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from collections import defaultdict
from djangotraining.settings import DEFAULT_FROM_EMAIL
from djangotraining.celery import app
import redis
from django.apps import apps

changes = []

admin_email = "huuloc061020030610@gmail.com"

redis_client = redis.Redis(host='djangotraining-redis-1', port=6379, db=0)

@shared_task(queue='celery', name='send_notification_email')
def send_notification_email(username, postTitle, post):
    if post == 1:
        redis_client.rpush('changes', f"CREATE,{username},{postTitle}")
    elif post == 2:
        redis_client.rpush('changes', f"UPDATE,{username},{postTitle}")
    else:
        redis_client.rpush('changes', f"DELETE,{username},{postTitle}")

@shared_task(queue='celery', name='send_hourly_notification_email')
def send_hourly_notification_email():
    subject = 'Thông báo các bài viết đã bị sửa đổi'
    message = ''

    changes = redis_client.lrange('changes', 0, -1)

    if not changes:
        message = 'Không có bài post nào bị thay đổi.'
    else:
        message = 'Các sự thay đổi trong trang Blog: \n\n'
        for change in changes:
            change_type, username, postTitle = change.decode().split(',')
            if change_type == 'CREATE':
                message += f'[CREATE] {postTitle} bởi {username} \n'
            elif change_type == 'UPDATE':
                message += f'[UPDATE] {postTitle} bởi {username} \n'
            elif change_type == 'DELETE':
                message += f'[DELETE] {postTitle} bởi {username} \n'
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [admin_email]
    send_mail(subject, message, from_email, recipient_list)
    
    redis_client.delete('changes')

@shared_task(queue='celery')
def publish_post(postID):
    Post = apps.get_model('blog', 'Post')
    post = Post.objects.get(pk=postID)
    post.postPublished = True
    post.save()