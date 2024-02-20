"""
URL configuration for newdjango project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
# from blog.views import CustomGoogleOAuth2CallbackView, google_callback
# from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
# from allauth.socialaccount.providers.oauth2.client import OAuth2Client
# from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView

# oauth2_callback = OAuth2CallbackView.as_view(callback_view=CustomGoogleOAuth2CallbackView)

urlpatterns = [
    path("blog/", include(('blog.urls', 'blog'), namespace='blog')),
    path("admin/", admin.site.urls),
    # path('accounts/', include('allauth.urls')),
    # re_path(r'^accounts/google/login/callback/$', google_callback, name='google_oauth2_callback'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns+=static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
    urlpatterns+= static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
