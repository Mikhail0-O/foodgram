from django.conf import settings
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        print(request.method)
        print(request.user.is_authenticated)
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated)
        )

    def has_object_permission(self, request, view, obj):
        print(request.method)
        if request.method in permissions.SAFE_METHODS:
            return True
        print(request.method)
        if request.method in ('PATCH', 'DELETE', 'POST'):
            print(obj.author == request.user)
            return obj.author == request.user
        return False
