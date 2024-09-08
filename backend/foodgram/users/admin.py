from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Follow

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar',)}),
)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('author', 'user')


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Follow, FollowAdmin)
