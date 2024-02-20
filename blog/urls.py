from django.urls import path

from .views import PostView, PostDetailView, PostUpdateView, PostCreateView, LoginView, PostDeleteView, CustomLogoutView, RegistrationView, UserView, UserUpdateView, create_posts_from_csv, search_result, LoadRepliesView
from .gg import google_callback, google_auth, send_email
from .fb import facebook_auth, facebook_callback
from .twitter import twitter_auth, twitter_callback
from .line import line_auth, line_callback
from django.urls import path
from blog.routing import websocket_urlpatterns


app_name = "blog"

urlpatterns = [
    path("main", PostView.as_view(), name="index"),
    path("users", UserView.as_view(), name="user"),
    path("detail/<int:pk>", PostDetailView.as_view(), name="detail"),
    path("create", PostCreateView.as_view(), name="blogCreate"),
    path("update/<int:pk>", PostUpdateView.as_view(), name = "blogUpdate"),
    path("updateUser/<int:pk>", UserUpdateView.as_view(), name = "userUpdate"),
    path("delete/<int:pk>", PostDeleteView.as_view(), name = "blogDelete"),
    path("login", LoginView.as_view(), name = "login"),
    path("logout", CustomLogoutView.as_view(), name = "logout"),
    path("registration", RegistrationView.as_view(), name="register"),
    path("csv", create_posts_from_csv, name="csv"),
    path("search_results", search_result, name="search"),
    path('load_replies/<int:pk>/', LoadRepliesView.as_view(), name='load_replies'),
    path('google', google_auth, name='google_auth'),
    path('google/callback', google_callback, name='google_callback'),
    path('facebook', facebook_auth, name='facebook_auth'),
    path('facebook/callback', facebook_callback, name='facebook_callback'),
    path('google/<int:pk>', send_email, name='recommendBlog'),
    path('twitter', twitter_auth, name ='twitter_auth'),
    path('twitter/callback', twitter_callback, name ='twitter_callback'),
    path('line', line_auth, name ='line_auth'),
    path('line/callback', line_callback, name ='line_callback'),
]

urlpatterns += websocket_urlpatterns
