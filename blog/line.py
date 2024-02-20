import requests
from django.shortcuts import redirect
from django.shortcuts import redirect
from .models import User, Channel, Post
from django.contrib.auth import login
from datetime import datetime, timedelta
from django.http import QueryDict
import requests
from .views import assign_role
from django.utils import timezone
from django.conf import settings
import string
import random
import jwt

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

def line_auth(request):
    state = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    line_login_url = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={settings.LINE_CHANNEL_ID}&redirect_uri={settings.LINE_REDIRECT_URI}&state={state}&scope=profile%20openid%20https://notify-api.line.me/api/notify"

    return redirect(line_login_url)

def line_callback(request):
    code = request.GET.get('code')
    print(code)
    state = request.GET.get('state')

    token_url = "https://api.line.me/oauth2/v2.1/token"
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.LINE_REDIRECT_URI,
        'client_id': settings.LINE_CHANNEL_ID,
        'client_secret': settings.LINE_CHANNEL_SECRET,
        "scope": "profile openid https://notify-api.line.me/api/notify"
    }

    response = requests.post(token_url, data=payload)
    token_data = response.json()
    print(token_data)
    id_token = token_data['id_token']
    access_token = token_data['access_token']

    # Sử dụng access token để lấy thông tin người dùng từ LINE
    # profile_url = "https://api.line.me/v2/profile"
    # headers = {
    #     'Authorization': f'Bearer {access_token}'
    # }

    # profile_response = requests.get(profile_url, headers=headers)
    # profile_data = profile_response.json()
    # print(profile_data)

    # # line_id = profile_data['id']
    # name = profile_data['displayName']
    # existing_users = User.objects.filter(username = name)
    # print(existing_users)

    url = 'https://api.line.me/oauth2/v2.1/verify'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'id_token': id_token,
        'client_id': settings.LINE_CHANNEL_ID
    }

    response = requests.post(url, headers=headers, data=data)

    profile_data = response.json()
    print(profile_data)

    line_id = profile_data['sub']
    name = profile_data['name']
    existing_users = User.objects.filter(username = name)
    print(existing_users)
    

    if existing_users.exists():
            user = existing_users.first()
            existing_channel = Channel.objects.filter(user = user, platform = 'LINE')
            if existing_channel.exists():
                channel = existing_channel.first()

                # check xem access_token hết hạn chưa
                if channel.expires_at < timezone.now():
                    access_token_date = generate_access_token(channel.refresh_token)
                    channel.access_token = access_token_date['access_token']
                    channel.expires_at = access_token_date['expires_at']
                    channel.save()

                print(check_token_scope(channel.access_token))
            else:
                refresh_token = token_data['refresh_token']
                print(refresh_token)
                access_token_date = generate_access_token(refresh_token)
                access_token = access_token_date['access_token']
                print(access_token)
                expires_at = access_token_date['expires_at']   

                channel = Channel.objects.create(
                    user = user, 
                    platform = 'LINE',
                    created = datetime.now(),
                    refresh_token = refresh_token,
                    access_token = access_token,
                    expires_at = expires_at,
                    line_id = line_id
                )
    else:
        refresh_token = token_data['refresh_token'] 
        print(refresh_token)
        access_token_date = generate_access_token(refresh_token)
        access_token = access_token_date['access_token']
        print(access_token)
        expires_at = access_token_date['expires_at']
        user = User.objects.create(
            username=name,
            first_name=name,
            last_name=name,
            date_joined=datetime.now(),
            is_active=1,
            blogCount=0
        )

        assign_role(user.id, 'Editor')

        channel = Channel.objects.create(
                user = user, 
                platform = 'LINE',
                created = datetime.now(),
                refresh_token = refresh_token,
                access_token = access_token,
                expires_at = expires_at,
                line_id = line_id
        )
        
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('blog:index')

def check_token_scope(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.post('https://api.line.me/oauth2/v2.1/verify', headers=headers)
    if response.status_code == 200:
        token_info = response.json()
        scopes = token_info.get('scope', '').split()
        return scopes