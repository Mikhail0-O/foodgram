from rest_framework import routers
from django.urls import include, path

from .views import (RecipeViewSet, get_token,
                    TagViewSet, IngredientViewSet,
                    FavouriteViewSet, CartViewSet,
                    download_shopping_cart)


v1_router = routers.DefaultRouter()
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
# v1_router.register(
#     r'recipes/(?P<recipe_id>\d+)/favorite',
#     FavouriteViewSet, basename='favorite'
# )

app_name = 'api'

urlpatterns = [
    path('v1/auth/token/login/', get_token, name='token'),
#     path('v1/auth/', include('djoser.urls.authtoken')),
    path('v1/recipes/download_shopping_cart/',
         download_shopping_cart,
         name='download_shopping_cart'),
    path('v1/recipes/<int:recipe_id>/favorite/',
         FavouriteViewSet.as_view({'delete': 'destroy',
                                   'post': 'create'}),
         name='recipe-favorite'),
    path('v1/recipes/<int:recipe_id>/shopping_cart/',
         CartViewSet.as_view({'delete': 'destroy',
                              'post': 'create'}),
         name='recipe-shopping_cart'),
    path('v1/', include(v1_router.urls)),
]
