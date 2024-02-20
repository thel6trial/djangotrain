import requests
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import login
from .models import User, Channel, Post
from datetime import datetime, timedelta
from .views import assign_role
from django.utils import timezone

def generate_access_token(refresh_token):
    # Create a new access token from the refresh token
    token_url = "https://api.twitter.com/oauth/access_token"
    token_params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.TWITTER_CONSUMER_KEY,
        "client_secret": settings.TWITTER_CONSUMER_SECRET
    }
    
    token_response = requests.post(token_url, data=token_params)
    response_data = dict(item.split('=') for item in token_response.text.split('&'))

    new_access_token = response_data.get('oauth_token')
    new_access_token_secret = response_data.get('oauth_token_secret')
    expires_in = response_data.get('expires_in') 
    
    current_time = datetime.now()
    expires_at = current_time + timedelta(seconds=int(expires_in)) if expires_in else None
    
    return {
        'access_token': new_access_token,
        'access_token_secret': new_access_token_secret,
        'expires_at': expires_at
    }

def twitter_auth(request):

    auth_url = f'https://api.twitter.com/oauth/authenticate?oauth_token={settings.TWITTER_CONSUMER_KEY}&oauth_callback={settings.TWITTER_REDIRECT_URI}&scope=offline_access'
    
    return redirect(auth_url)

def twitter_callback(request):
    oauth_token = request.GET.get('oauth_token')
    oauth_verifier = request.GET.get('oauth_verifier')

    token_url = 'https://api.twitter.com/oauth/access_token'
    token_params = {
        'oauth_consumer_key': settings.TWITTER_CONSUMER_KEY,
        'oauth_token': oauth_token,
        'oauth_verifier': oauth_verifier,
    }
    token_headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(token_url, data=token_params, headers=token_headers)
    response_data = dict(item.split('=') for item in response.text.split('&'))

    print(response_data)

    access_token = response_data.get('oauth_token')

    profile_url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
    auth_header = {'Authorization': 'Bearer {}'.format(access_token)}
    profile_response = requests.get(profile_url, headers=auth_header)
    profile_data = profile_response.json()
    
    print(profile_data)

    username = profile_data['screen_name']
    name = profile_data['name']

    existing_users = User.objects.filter(username = username)

    if existing_users.exists():
            user = existing_users.first()
            existing_channel = Channel.objects.filter(user = user, platform = 'Twitter')
            if existing_channel.exists():
                channel = existing_channel.first()

                # check xem access_token hết hạn chưa
                if channel.expires_at < timezone.now():
                    access_token_date = generate_access_token(channel.refresh_token)
                    channel.access_token = access_token_date['access_token']
                    channel.expires_at = access_token_date['expires_at']
                    channel.save()
            else:
                refresh_token = response_data.get('oauth_token')  
                print(refresh_token)
                access_token_date = generate_access_token(refresh_token)
                access_token = access_token_date['access_token']
                print(access_token)
                expires_at = access_token_date['expires_at']   

                channel = Channel.objects.create(
                    user = user, 
                    platform = 'Twitter',
                    created = datetime.now(),
                    refresh_token = refresh_token,
                    access_token = access_token,
                    expires_at = expires_at
                )
    else:
        refresh_token = response_data.get('oauth_token') 
        print(refresh_token)
        access_token_date = generate_access_token(refresh_token)
        access_token = access_token_date['access_token']
        print(access_token)
        expires_at = access_token_date['expires_at']
        user = User.objects.create(
            username=username,
            first_name=name,
            last_name=name,
            date_joined=datetime.now(),
            is_active=1,
            blogCount=0
        )

        assign_role(user.id, 'Editor')

        channel = Channel.objects.create(
                user = user, 
                platform = 'Twitter',
                created = datetime.now(),
                refresh_token = refresh_token,
                access_token = access_token,
                expires_at = expires_at
        )
        
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('blog:index')


    # Redirect the user to the desired page
    return redirect('blog:index')