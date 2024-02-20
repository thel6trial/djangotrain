from django import template

register = template.Library()

@register.filter
def get_user_role(user):
    return user.groups.first().name if user.groups.exists() else None