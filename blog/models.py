from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from ckeditor.fields import RichTextField

class User(AbstractUser):
    #userID = models.IntegerField(primary_key = True)
    # userName = models.CharField(max_length = 200)
    # password = models.CharField(max_length = 200)
    birtday = models.CharField("Birthday", max_length = 210)
    blogCount = models.IntegerField("Number of Blogs", default = 0)
    # id_token = models.TextField("ID Token", blank=True, null=True)
    # refresh_token = models.TextField("Refresh Token", blank=True, null=True)
    # access_token = models.TextField("Access Token", blank=True, null=True)
    # expires_at = models.DateTimeField("Expire of Access Token", blank=True, null=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',  
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username
    
    class Meta():
        db_table = "user_seq"


class Channel(models.Model):
    id = models.AutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE)

    platform = models.CharField("Name of the platform", max_length = 100, blank = True, null = True)
    created = models.DateTimeField("Created at", blank = True, null = True)
    refresh_token = models.TextField("Refresh Token", blank=True, null=True)
    access_token = models.TextField("Access Token", blank=True, null=True)
    expires_at = models.DateTimeField("Expire of Access Token", blank=True, null=True)
    line_id = models.TextField("Line ID of User", blank=True, null=True)

    class Meta():
        db_table = "channel_seq"

class Post(models.Model):

    postID = models.IntegerField(primary_key = True)
    postTitle = models.CharField("Post Title", max_length = 200)
    postContent = RichTextField("Post Content")

    postPublished = models.BooleanField(default = True)
    postDate = models.DateTimeField("Date Published")
    postImage = models.ImageField(upload_to='images/', null=True, blank=True)
    postImageAWS = models.TextField(null=True, blank=True)

    user = models.ForeignKey(User, on_delete = models.CASCADE)

    def __str__(self):
        return self.postTitle
    
    class Meta():
        db_table = "post_seq"

class DeletedPostNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=False)

    class Meta():
        db_table = "noti_seq"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    post = models.ForeignKey(Post, on_delete = models.CASCADE)

    id = models.AutoField(primary_key = True)
    parent = models.ForeignKey('self', on_delete = models.CASCADE, null = True, blank = True, related_name="replies")
    content = models.TextField("Nội dung bình luận")
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.content
    
    class Meta:
        db_table = "comment_seq"