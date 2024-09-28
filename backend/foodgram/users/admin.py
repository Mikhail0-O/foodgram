from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomUser, Follow

BaseUserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar',)}),
)


class UserAdmin(BaseUserAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'is_staff'
    )


class FollowAdmin(admin.ModelAdmin):
    list_display = ('author', 'user')


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Follow, FollowAdmin)
