from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth import get_user_model


class UserAdmin(ModelAdmin):
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
