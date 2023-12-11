from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group


class UserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_superuser',
        'is_active'
    )
    list_filter = ('email', 'username',)


admin.site.register(get_user_model(), UserAdmin)
admin.site.unregister(Group)
