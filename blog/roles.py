from rolepermissions.roles import AbstractUserRole
from django.contrib.auth.models import Group, Permission

class Admin(AbstractUserRole):
    available_permissions = {
        'view_post': True,
        'change_post': True,
        'delete_post': True,
        'add_post': True,
        'view_user': True,
        'add_user': True,
        'change-user': True,
        'delete_user': True,
    }

    @staticmethod
    def assign_role_to_user(user):
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        for permission_name, has_permission in Admin.available_permissions.items():
            if has_permission:
                permissions = Permission.objects.filter(codename=permission_name)
                for permission in permissions:
                    admin_group.permissions.add(permission)
        user.groups.add(admin_group)

    
    
class Viewer(AbstractUserRole):
    available_permissions = {
        'view_post': True,
        'change_post': False,
        'delete_post': False,
        'add_post': False,
    }
    
    @staticmethod
    def assign_role_to_user(user):
        viewer_group, _ = Group.objects.get_or_create(name='Viewer')
        for permission_name, has_permission in Viewer.available_permissions.items():
            if has_permission  == True:
                permissions = Permission.objects.filter(codename=permission_name)
                for permission in permissions:
                    viewer_group.permissions.add(permission)
        user.groups.add(viewer_group)

class Editor(AbstractUserRole):
    available_permissions = {
        'view_post': True,
        'change_post': True,
        'delete_post': True,
        'add_post': True,
    }

    @staticmethod
    def assign_role_to_user(user):
        editor_group, _ = Group.objects.get_or_create(name='Editor')
        for permission_name, has_permission in Editor.available_permissions.items():
            if has_permission  == True:
                permissions = Permission.objects.filter(codename=permission_name)
                for permission in permissions:
                    editor_group.permissions.add(permission)
        user.groups.add(editor_group)

    