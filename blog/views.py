from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View, DeleteView
from .models import Post, User, DeletedPostNotification, Comment, Channel
from django.urls import reverse_lazy
from .forms import PostCreateForm, UserCreateForm, CommentForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .roles import Admin, Viewer, Editor
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, logout
from datetime import datetime, timedelta
from django.http import QueryDict
# from .middleware import PermissionDeniedCustom
from django.contrib import messages
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .tasks import send_notification_email
import logging
import csv
from django.template.response import TemplateResponse
from django.utils.html import escape  
from blog.tasks import publish_post
import requests
import google.oauth2.id_token
from google.auth.transport import requests as google_requests
from django.utils import timezone
from googleapiclient.discovery import build
from django.contrib import messages
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
from google.oauth2 import credentials
from google.oauth2 import service_account
from google.oauth2 import id_token
from django.conf import settings
from google.auth.transport import requests as google_requests
from linebot import LineBotApi
from linebot.models import TextSendMessage

def assign_role(id, role):
    user = User.objects.get(pk = id)
    if role == 'Admin':
        Admin.assign_role_to_user(user)
    elif role == 'Viewer':
        Viewer.assign_role_to_user(user)
    elif role == 'Editor':
        Editor.assign_role_to_user(user)

class PostView(LoginRequiredMixin, ListView):
    model = Post
    context_object_name = "post_list"
    template_name = "blog/index.html"
    paginate_by = 4

    def dispatch(self, request, *args, **kwargs):

        user = request.user
        print(user.id)
        print(self.check_permissions(user.id))

        if user.id != 0 and self.check_permissions(user.id) == True:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
        
    def check_permissions(self, user_id):
        
        user = User.objects.get(pk = user_id)
        return user.has_perm('blog.view_post')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.has_perm('blog.view_user'):
            notifications = DeletedPostNotification.objects.filter(is_displayed=False)
            for notification in notifications:
                messages.info(self.request, notification.message)
                notification.is_displayed = True
                notification.save()
            
        for message in messages.get_messages(self.request):
            print(message)
        context['messages'] = messages.get_messages(self.request)
        return context
    
class UserView(ListView):
    model = User
    context_object_name = "user_list"
    template_name = "user/user_list.html"

    def dispatch(self, request, *args, **kwargs):

        user = request.user
        print(user.id)
        print(self.check_permissions(user.id))

        if user.id != 0 and self.check_permissions(user.id) == True:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
        
    def check_permissions(self, user_id):
        
        user = User.objects.get(pk = user_id)
        return user.has_perm('blog.view_user')

class PostDetailView(LoginRequiredMixin, View):
    model = Post
    template_name = "blog/blog_detail.html"
    login_url = "{% url 'blog:login' %}"
    form_class = CommentForm

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs['pk']
        post = Post.objects.get(postID = post_id)
        try:
            comments = Comment.objects.filter(post = post, parent = None)
        except Comment.DoesNotExist:
            comments = None

        return render(request, 'blog/blog_detail.html', {'post': post, 'comments': comments})
    
    def post(self, request, *args, **kwargs):
        post_id = self.kwargs['pk']
        post = Post.objects.get(postID = post_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data.get('content')
            user = request.user
            parent_id = request.POST.get('parent')
            if parent_id:
                parent_comment = Comment.objects.get(id=parent_id)
                comment = Comment.objects.create(user=user, post=post, content=content, parent=parent_comment)
            else:
                comment = Comment.objects.create(user=user, post=post, content=content)
            return redirect('blog:detail', pk=post.postID)

        try:
            comments = Comment.objects.filter(post = post)
        except Comment.DoesNotExist:
            comments = None

        return render(request, 'blog/blog_detail.html', {'post': post, 'comments': comments})
    
class LoadRepliesView(View):
    def get(self, request, *args, **kwargs):
        reply_id = self.kwargs['pk']
        reply = Comment.objects.get(id=reply_id)
        replies = reply.replies.all() 

        return render(request, 'blog/replies.html', {'replies': replies})
    
    def post(self, request, *args, **kwargs):
        reply_id = self.kwargs['pk']
        reply = Comment.objects.get(id=reply_id)
        form = CommentForm(request.POST)
        post = reply.post
        user = reply.user
        replies = reply.replies.all() 
        if form.is_valid():
            content = form.cleaned_data.get('content')
            comment = Comment.objects.create(user=user, post=post, content=content, parent = reply)

        return render(request, 'blog/replies.html', {'replies': replies})
    

class PostDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy("blog:index")

    def dispatch(self, request, *args, **kwargs):

        user = request.user
        print(user.id)
        print(self.check_permissions(user.id))

        if user.id != 0 and self.check_permissions(user.id) == True:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
    
    def check_permissions(self, user_id):
        
        user = User.objects.get(pk = user_id)
        return user.has_perm('blog.delete_post')
    
# @receiver(post_delete, sender=Post)
# def post_deleted(sender, request, instance, **kwargs):
#     user = request.user
#     DeletedPostNotification.objects.create(
#         user=user,
#         message=f"{user.username} đã xóa một bài viết: {instance.postTitle}"
#     )

#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)("admin_group", {"type": "send_notification", "message": f"{user.username} đã xóa một bài viết: {instance.postTitle}"})

#     send_notification_email.delay(user.username, instance.postTitle, 3)

class PostUpdateView(LoginRequiredMixin, View):
    model = Post
    template_name = "blog/blog_change.html"
    fields = ["postID","postTitle", "postContent", "postDate", "postImage"]
    success_url = reverse_lazy("blog:index")
    form_class = PostCreateForm

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        post = get_object_or_404(Post, postID=pk)
        form = self.form_class(instance=post)
        return render(request, self.template_name, {'form': form, 'post': post})
    
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=pk)
        form = self.form_class(request.POST, request.FILES, instance=post)
        print(form)
        # if request.headers.get('HX-POST') == 'true':
        #     if form.is_valid():
        #         form.save()
        #         return TemplateResponse(request, self.template_name, {'form': form, 'post': post})
            
        # else:
        if form.is_valid():
            form.save()
            return redirect('blog:index')
            
        return render(request, self.template_name, {'form': form})
    
    
    def dispatch(self, request, pk, *args, **kwargs):

        post = get_object_or_404(Post, pk=pk)
        user = request.user
        print(user.id)
        print(self.check_permissions(user.id))

        if user == post.user and self.check_permissions(user.id) == True:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
    
    def check_permissions(self, user_id):
        
        user = User.objects.get(pk = user_id)
        return user.has_perm('blog.change_post')
    
class UserUpdateView(LoginRequiredMixin, View):
    model = User
    template_name = "user/user_change.html"
    fields = ["username", "first_name", "last_name", "birtday"]
    success_url = reverse_lazy("blog:user")
    form_class = UserCreateForm

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        user = get_object_or_404(User, id=pk)
        form = self.form_class(instance=user)
        return render(request, self.template_name, {'form': form, 'user': user})
    
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        user = get_object_or_404(User, id=pk)
        form = self.form_class(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:user')

        return render(request, self.template_name, {'form': form})
    
    def dispatch(self, request, pk, *args, **kwargs):

        user = request.user
        print(user.id)
        print(self.check_permissions(user.id))

        if self.check_permissions(user.id) == True:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
    
    def check_permissions(self, user_id):
        
        user = User.objects.get(pk = user_id)
        return user.has_perm('blog.view_user')

class PostCreateView(LoginRequiredMixin, View):
    template_name = "blog/blog_change.html"
    login_url = "{% url 'blog:login' %}"

    def get(self, request):
        form = PostCreateForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PostCreateForm(request.POST)
        user = request.user

        if form.is_valid():
            postTitle = form.cleaned_data['postTitle']
            if Post.objects.filter(postTitle=postTitle).exists():
                form.add_error('postTitle', 'Title already exists.')
            else:

                user.blogCount += 1
                user.save()

                schedule_post = request.POST.get("schedulePost")
            
                if schedule_post:
                    schedule_date_str = request.POST.get("scheduleDate")

                    post1 = Post(
                    postID=form.cleaned_data['postID'],
                    postTitle=form.cleaned_data['postTitle'],
                    postContent=form.cleaned_data['postContent'],
                    postDate=form.cleaned_data['postDate'],
                    postImage=form.cleaned_data['postImage'],
                    postPublished = False,
                    user=user
                    )
                
                    post1.save()
                    if schedule_date_str:
                        schedule_date = datetime.strptime(schedule_date_str, "%Y-%m-%dT%H:%M")
                        current_date = datetime.now()

                        if schedule_date > current_date:
                        # Lập lịch công việc Celery để đăng bài
                            publish_post.apply_async(args=(post1.postID,), eta=schedule_date)

                            echannel = Channel.objects.filter(user = user, platform="Google")

                            if echannel.exists():
                                channel = echannel.first()
                                access_token = channel.access_token
                                refresh_token = channel.refresh_token
                                event_title = 'Đăng bài trên blog'
                                event_description = f'Bài đăng: {post1.postTitle}'
                                event_start_datetime = schedule_date
                                event_end_datetime = schedule_date  

                                event_id = create_calendar_event(access_token, refresh_token, event_title, event_description, event_start_datetime, event_end_datetime)

                                messages.success(request, f'Bạn đã lên lịch đăng bài thành công trong Calendar với id = {event_id}.')
                else:
                    post1 = Post(
                    postID=form.cleaned_data['postID'],
                    postTitle=form.cleaned_data['postTitle'],
                    postContent=form.cleaned_data['postContent'],
                    postDate=form.cleaned_data['postDate'],
                    postImage=form.cleaned_data['postImage'],
                    postPublished = True,
                    user=user
                    )
                
                    post1.save()
                        
                return redirect('blog:index')

        return render(request, self.template_name, {'form': form})
    
    def dispatch(self, request, *args, **kwargs):

        user = request.user
        print(user.id)
        print(self.check_permissions(user.id))

        if user.id != 0 and self.check_permissions(user.id) == True:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
    
    def check_permissions(self, user_id):
        
        user = User.objects.get(pk = user_id)
        return user.has_perm('blog.add_post')
    
@receiver(post_save, sender=Post)
def post_init(sender, instance, created, **kwargs):
    user = User.objects.get(pk=instance.user_id)
    print(user.username)
    print(user.id)
    if created:
        DeletedPostNotification.objects.create(
            user=user,
            message=f"{user.username} đã tạo một bài viết: {instance.postTitle}"
        )
        channel_layer = get_channel_layer() 
        async_to_sync(channel_layer.group_send)("admin_group", {"type": "send_notification", "message": f"{user.username} đã tạo một bài viết: {instance.postTitle}"})

        send_notification_email.delay(user.username, instance.postTitle, 1)

        existing_channel = Channel.objects.filter(user = user, platform = "LINE")
        print(existing_channel)
        
        channel = existing_channel.first()

        response = send_line_notification(channel, f"{user.username} đã tạo một bài viết: {instance.postTitle} thành công trên hệ thống")
        print(response)

    else:
        DeletedPostNotification.objects.create(
            user=user,
            message=f"{user.username} đã sửa một bài viết: {instance.postTitle}"
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("admin_group", {"type": "send_notification", "message": f"{user.username} đã sửa một bài viết: {instance.postTitle}"})

        send_notification_email.delay(user.username, instance.postTitle, 2)

        existing_channel = Channel.objects.filter(user = user, platform = "LINE")
        print(existing_channel)
        
        channel = existing_channel.first()

        response = send_line_notification(channel, f"{user.username} đã sửa một bài viết: {instance.postTitle} thành công trên hệ thống")
        print(response)
     
class LoginView(View):
    template_name = "registration/login.html"
    logger = logging.getLogger(__name__)

    def get(self, request):
        self.logger.info("GET Request Successfully")
        return render(request, self.template_name)
    
    def post(self, request):
        self.logger.debug("POST request recieved")
        username = request.POST.get('username')
        # password = request.POST.get('password')

        if username is None:
            return self.post(request)
        else:
            if User.objects.filter(username = username).exists():
            
                user = User.objects.get(username = username)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                self.logger.info("Login successfully")

                return redirect('blog:index')  
            else:
                self.logger.warning("Login failed")
                error_message = "Invalid username or password."
                return render(request, 'registration/login.html', {'error_message': error_message})
        
class CustomLogoutView(View):
    next_page = reverse_lazy('blog:login')

    def dispatch(self, request, *args, **kwargs):
        logout(request)  # Xóa thông tin người dùng khỏi request
        return redirect(self.next_page)
    
class RegistrationView(View):
    template_name = "registration/register.html"
    logger = logging.getLogger(__name__)

    def get(self, request):
        self.logger.info("Recieved GET method successfully")
        return render(request, self.template_name)

    def post(self, request):

        self.logger.debug("POST request recieved")
        form = QueryDict(request.POST.urlencode())

        username = form.get('username')
        if User.objects.filter(username = username).exists():
            form.add_error('username', 'Username already exists.')
        else:
            user = User(
                id = form.get('id'),
                username = form.get('username'),
                password = form.get('password'),
                birtday=form.get('birtday'),
                first_name=form.get('first_name'),
                last_name = form.get('last_name'),
                date_joined = datetime.now(),
                is_active = 1,
                blogCount = 0
            )
            
            user.save()

            role = form.get('role')
            print(role)
            assign_role(form.get('id'), role)
            return redirect('blog:login')

        self.logger.warning("Registration User failed")
        return render(request, self.template_name, {'form': form})

def create_posts_from_csv(request):
    file_path = 'blog/static/Post1.csv'
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip the header row
        for row in reader:
            post_id = row[0]
            post_title = row[1]
            post_content = row[2]
            post_date = datetime.now()
            username = row[4]
            
            post = Post(
                    postID=post_id,
                    postTitle=post_title,
                    postContent=post_content,
                    postDate=post_date,
                    user = User.objects.get(username = username)
                )
            post.save()
            print(f"Post with ID {post_id} created successfully.")

    return redirect('blog:index')  

def search_result(request):
    query = request.POST.get('searchName')
    post_list = Post.objects.filter(postTitle = query)
    return TemplateResponse(request, "blog/index.html", {"post_list": post_list})

def facebook_auth(request):
    facebook_login_url = f"https://www.facebook.com/v12.0/dialog/oauth?client_id={settings.FACEBOOK_APP_ID}&redirect_uri={settings.FACEBOOK_REDIRECT_URI}&response_type=code&scope=email"
    return redirect(facebook_login_url)

def facebook_callback(request):
    code = request.GET.get('code')
    token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
    token_params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "code": code
    }

    # GET để lấy mã thông báo truy cập
    token_response = requests.get(token_url, params=token_params)
    token_data = token_response.json()
    access_token = token_data['access_token']

    # GET để lấy thông tin người dùng từ mã thông báo truy cập
    user_url = "https://graph.facebook.com/v12.0/me"
    user_params = {
        "access_token": access_token,
        "fields": "id,name,email"
    }

    user_response = requests.get(user_url, params=user_params)
    user_data = user_response.json()
    email = user_data['email']
    name = user_data['name']

    existing_users = User.objects.filter(username=email)

    if existing_users.exists():
        user = existing_users.first()
        user.id_token = access_token
        user.save()

    else:
        user = User.objects.create(
            username=email,
            first_name=name,
            last_name=name,
            email=email,
            date_joined=datetime.now(),
            is_active=1,
            blogCount=0,
            id_token=access_token
        )

        assign_role(user.id, 'Editor')
    
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('blog:index')


def create_calendar_event(access_token, refresh_token, event_title, event_description, event_start_datetime, event_end_datetime):
    
    access_token_credentials = credentials.Credentials(access_token)

    service = build('calendar', 'v3', credentials=access_token_credentials)

    event = {
        'summary': event_title,
        'description': event_description,
        'start': {
            'dateTime': event_start_datetime.isoformat(),
            'timeZone': 'Asia/Ho_Chi_Minh',  
        },
        'end': {
            'dateTime': event_end_datetime.isoformat(),
            'timeZone': 'Asia/Ho_Chi_Minh',  
        },
    }

    calendar_event = service.events().insert(calendarId='primary', body=event).execute()

    return calendar_event['id'] 

def generate_access_token(refresh_token):
    # Tạo access token mới từ refresh token
    token_url = "https://api.line.me/oauth2/v2.1/token"
    token_payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.LINE_CHANNEL_ID,
        "client_secret": settings.LINE_CHANNEL_SECRET
    }

    token_response = requests.post(token_url, data=token_payload)
    token_data = token_response.json()

    new_access_token = token_data['access_token']
    expires_in = token_data['expires_in']

    current_time = datetime.now()
    expires_at = current_time + timedelta(seconds=expires_in)

    return {
        'access_token': new_access_token,
        'expires_at': expires_at
    }

def send_line_notification(channel, message):

    print(message)
        
   

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + settings.LINE_MESSAGE_ACCESS
    }
    data = {
        'to': channel.line_id,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response
