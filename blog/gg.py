from django.shortcuts import redirect
from .models import User, Channel, Post
from django.contrib.auth import login
from datetime import datetime, timedelta
from django.http import QueryDict
import requests
import google.oauth2.id_token
from django.conf import settings
from google.auth.transport import requests as google_requests
from .views import assign_role
from django.utils import timezone
from googleapiclient.discovery import build
from django.contrib import messages
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
from google.oauth2 import credentials
import base64
from google.oauth2 import service_account
from email.message import EmailMessage

def google_auth(request):
    # Chuyển hướng người dùng đến trang đăng nhập của Google
    google_login_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&response_type=code&scope=email%20profile%20https://www.googleapis.com/auth/gmail.send%20https://www.googleapis.com/auth/calendar&access_type=offline"
    return redirect(google_login_url)

def generate_access_token(refresh_token):
    # tạo access_token mới từ refresh_token
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "refresh_token": refresh_token,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        # "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar",
        "grant_type": "refresh_token"
    }
    
    token_response = requests.post(token_url, data=token_payload)
    token_data = token_response.json()
    print(token_data)
    
    new_access_token = token_data['access_token']
    expires_in = token_data['expires_in']
    
    current_time = datetime.now()
    expires_at = current_time + timedelta(seconds=expires_in)
    
    return {
        'access_token': new_access_token,
        'expires_at': expires_at
    }

def google_callback(request):
    code = request.GET.get('code')
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        'access_type': 'offline',
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar"
    }

    # POST to get id_token
    token_response = requests.post(token_url, data=token_payload)
    token_data = token_response.json()
    print(token_data)
    id_token_str = token_data['id_token']
    print(check_token_scope(token_data['access_token']))

    # Xác thực mã thông báo truy cập
    request_obj = google_requests.Request()
    print(id_token_str)

    idinfo = google.oauth2.id_token.verify_oauth2_token(id_token_str, request_obj)

    if idinfo['aud'] == settings.GOOGLE_CLIENT_ID:

        email = idinfo['email']
        name = idinfo['name']

        existing_users = User.objects.filter(username=email)

        if existing_users.exists():
            user = existing_users.first()
            existing_channel = Channel.objects.filter(user = user, platform = 'Google')
            if existing_channel.exists():
                channel = existing_channel.first()

                # check xem access_token hết hạn chưa
                if channel.expires_at < timezone.now():
                    access_token_date = generate_access_token(channel.refresh_token)
                    channel.access_token = access_token_date['access_token']
                    channel.expires_at = access_token_date['expires_at']
                    channel.save()
            else:
                refresh_token = token_data['refresh_token']
                print(refresh_token)
                access_token_date = generate_access_token(refresh_token)
                access_token = access_token_date['access_token']
                print(access_token)
                expires_at = access_token_date['expires_at']   

                channel = Channel.objects.create(
                    user = user, 
                    platform = 'Google',
                    created = datetime.now(),
                    refresh_token = refresh_token,
                    access_token = access_token,
                    expires_at = expires_at
                )
        else:
            refresh_token = token_data['refresh_token']
            print(refresh_token)
            access_token_date = generate_access_token(refresh_token)
            access_token = access_token_date['access_token']
            print(access_token)
            expires_at = access_token_date['expires_at']
            user = User.objects.create(
                username=email,
                first_name=name,
                last_name=name,
                email=email,
                date_joined=datetime.now(),
                is_active=1,
                blogCount=0
            )

            assign_role(user.id, 'Editor')

            channel = Channel.objects.create(
                    user = user, 
                    platform = 'Google',
                    created = datetime.now(),
                    refresh_token = refresh_token,
                    access_token = access_token,
                    expires_at = expires_at
                )
        
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('blog:index')


# task để gửi email cho người bạn
def send_email(request, pk):
    user = request.user 
    channel = Channel.objects.get(user = user, platform="Google")
    refresh_token = channel.refresh_token
    access_token = channel.access_token

    # check xem access_token còn hạn khộng
    if channel.expires_at < timezone.now():
        access_token_date = generate_access_token(refresh_token)
        access_token = access_token_date['access_token']
        expires_at = access_token_date['expires_at']

        channel.access_token = access_token
        channel.expires_at  = expires_at

        channel.save()

    print(check_token_scope(access_token))

    credentials_auth = Credentials(access_token)
    print(credentials_auth)
    service = googleapiclient.discovery.build('gmail', 'v1', credentials=credentials_auth)

    post = Post.objects.get(pk = pk)

    # Tạo email message
    email = request.POST.get('email')  

    message = EmailMessage()
    message.set_content(f"Dưới đây là bài post: {post.postTitle}\n\nLink: {request.build_absolute_uri()}")
    message["To"] = email
    message["From"] = user.email
    message["Subject"] = "Gợi ý Post bổ ích từ Website Blog6"
    print(message)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}

    service.users().messages().send(
           userId='me',
           body=create_message
    ).execute()

    messages.success(request, f'Bạn đã gửi thành công cho email {email}.')

    return redirect('blog:detail', pk = pk)

def send_message(service, sender, userId, recipient, subject, message_text):
    message = create_message(sender, recipient, subject, message_text)
    service.users().messages().send(userId='me', body=message).execute()

def create_message(sender, recipient, subject, message_text):
    message = f"From: {sender}\nTo: {recipient}\nSubject: {subject}\n\n{message_text}"

    message_bytes = message.encode('utf-8')
    encoded_message = base64.urlsafe_b64encode(message_bytes).decode('utf-8')
    
    return {'raw': encoded_message}

def check_token_scope(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.post('https://www.googleapis.com/oauth2/v1/tokeninfo', headers=headers)
    if response.status_code == 200:
        token_info = response.json()
        scopes = token_info.get('scope', '').split()
        return scopes
    else:
        # Handle error
        return None