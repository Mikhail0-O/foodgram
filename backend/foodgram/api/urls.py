from django.urls import include, path
from rest_framework import routers

from .views import (AvatarUserViewSet, CartViewSet, FavouriteViewSet,
                    FollowDestroyUpdateViewSet, FollowViewSet,
                    IngredientViewSet, RecipeLinkView, RecipeViewSet,
                    TagViewSet, UserViewSet, delete_token,
                    download_shopping_cart, get_token)


v1_router = routers.DefaultRouter()
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('users', UserViewSet)

app_name = 'api'

urlpatterns = [
    path('auth/token/login/', get_token, name='get_token'),
    path('auth/token/logout/', delete_token, name='delete_token'),
    path('recipes/download_shopping_cart/',
         download_shopping_cart,
         name='download_shopping_cart'),
    path('recipes/<int:recipe_id>/favorite/',
         FavouriteViewSet.as_view({'delete': 'destroy',
                                   'post': 'create'}),
         name='recipe-favorite'),
    path('recipes/<int:recipe_id>/shopping_cart/',
         CartViewSet.as_view({'delete': 'destroy',
                              'post': 'create'}),
         name='recipe-shopping_cart'),
    path('users/me/avatar/',
         AvatarUserViewSet.as_view({'delete': 'destroy',
                                    'put': 'update'}),
         name='users-avatar'),
    path('users/subscriptions/',
         FollowViewSet.as_view({'get': 'list'}),
         name='user-follow-get'),
    path('users/<int:user_id>/subscribe/',
         FollowDestroyUpdateViewSet.as_view({'delete': 'destroy',
                                             'post': 'create'}),
         name='user-follow-delete-post'),
    path('recipes/<int:id>/get-link/',
         RecipeLinkView.as_view(), name='recipe-get-link'),
    path('', include(v1_router.urls)),
]
