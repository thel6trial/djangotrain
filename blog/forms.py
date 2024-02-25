from django import forms
from .models import Post, User, Comment
from ckeditor.fields import RichTextFormField
from django.utils import timezone
from django.core.exceptions import ValidationError

class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["postID", "postTitle", "postContent", "postDate", "postImage"]

    def clean(self):
        cleaned_data = super().clean()
        post_date = cleaned_data.get("postDate")
        postTitle = cleaned_data.get("postTitle")
        postContent = cleaned_data.get("postContent")
        postImage = cleaned_data.get("postImage")

        if post_date and post_date > timezone.now():
            self.add_error("postDate", "The post date cannot be in the future.")

        if postTitle and len(postTitle) < 5:
            self.add_error("postTitle", "The post title is too short.")

        if postContent and len(postContent) > 100:
            self.add_error("postContent", "The post content is too long.")

        return cleaned_data

class UserCreateForm(forms.ModelForm):
    postContent = forms.CharField(widget=RichTextFormField()) 
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "birtday"]

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "password", "first_name", "last_name", "birtday"]

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ["content", "parent"]