from rest_framework import routers
from django.urls import include, path

from .views import RecipeViewSet, get_token

urlpatterns = [
    path('v1/recipes/', RecipeViewSet.as_view(
        {'get': 'list'})),
    path('v1/auth/token/', get_token, name='token'),
]
