from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, User, Channel
from django.contrib.auth import login
from datetime import datetime, timedelta
from django.utils import timezone
import requests
from django.conf import settings
from .views import assign_role

def facebook_auth(request):
    facebook_login_url = f"https://www.facebook.com/v12.0/dialog/oauth?client_id={settings.FACEBOOK_APP_ID}&redirect_uri={settings.FACEBOOK_REDIRECT_URI}&response_type=code&scope=email"
    return redirect(facebook_login_url)

def generate_access_token(refresh_token):
    refresh_url = "https://graph.facebook.com/v12.0/oauth/access_token"
    refresh_params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "grant_type": "fb_exchange_token",
        "fb_exchange_token": refresh_token
    }

    refresh_response = requests.get(refresh_url, params=refresh_params)
    refresh_data = refresh_response.json()
    access_token = refresh_data['access_token']
    expires_in = refresh_data['expires_in']

    current_time = datetime.now()
    expires_at = current_time + timedelta(seconds=expires_in)
    
    return {
        'access_token': access_token,
        'expires_at': expires_at
    }


def facebook_callback(request):
    code = request.GET.get('code')
    token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
    token_params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "code": code,
        "scope": "email public_profile offline_access"
    }

    # GET để lấy mã thông báo truy cập
    token_response = requests.get(token_url, params=token_params)
    token_data = token_response.json()
    print(token_data)
    refresh_token = token_data['access_token']

    # GET để lấy thông tin người dùng từ mã thông báo truy cập
    user_url = "https://graph.facebook.com/v12.0/me"
    user_params = {
        "access_token": refresh_token,
        "fields": "id,name,email"
    }

    user_response = requests.get(user_url, params=user_params)
    user_data = user_response.json()
    email = user_data['email']
    name = user_data['name']

    existing_users = User.objects.filter(username=email)

    if existing_users.exists():
        user = existing_users.first()
        existing_channel = Channel.objects.filter(user = user, platform = 'Facebook')
        if existing_channel.exists():
            channel = existing_channel.first()
            if channel.expires_at < timezone.now():
                access_token_date = generate_access_token(channel.refresh_token)
                channel.access_token = access_token_date['access_token']
                channel.expires_at = access_token_date['expires_at']

                channel.save()
        else:
            access_token_date = generate_access_token(refresh_token)
            access_token = access_token_date['access_token']
            print(access_token)
            expires_at = access_token_date['expires_at']
            channel = Channel.objects.create(
                user = user, 
                platform = 'Facebook',
                created = datetime.now(),
                refresh_token = refresh_token,
                access_token = access_token,
                expires_at = expires_at 
            )

    else:
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
            blogCount=0,
        )

        assign_role(user.id, 'Editor')

        channel = Channel.objects.create(
                user = user, 
                platform = 'Facebook',
                created = datetime.now(),
                refresh_token = refresh_token,
                access_token = access_token,
                expires_at = expires_at 
            )
    
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('blog:index')

