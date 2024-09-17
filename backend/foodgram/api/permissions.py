from django.conf import settings
from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated)
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method in ('PATCH', 'DELETE', 'POST'):
            return obj.author == request.user
        return False


class IsCurrentUserOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'me':
            return obj == request.user
        return request.method in ('GET', 'HEAD', 'OPTIONS')
