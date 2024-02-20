from django.contrib import admin

from .models import Post, User, Comment, Channel

admin.site.register(Post)
admin.site.register(Comment)

class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "username", "password", "first_name", "last_name", "blogCount"]

class ChannelAdmin(admin.ModelAdmin):
    list_display = ["user", "platform", "created", "expires_at"]

admin.site.register(User, UserAdmin)
admin.site.register(Channel, ChannelAdmin)