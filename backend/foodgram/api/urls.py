from rest_framework import routers
from django.urls import include, path

from .views import RecipeViewSet, get_token, TagViewSet, IngredientViewSet, FavouriteViewSet


v1_router = routers.DefaultRouter()
v1_router.register(r'recipes', RecipeViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
# v1_router.register(
#     r'recipes/(?P<recipe_id>\d+)/favorite',
#     FavouriteViewSet, basename='favorite'
# )

app_name = 'api'

urlpatterns = [

    # path('v1/tags/', TagViewSet.as_view(
    #     {'get': 'list'})),
    path('v1/auth/token/', get_token, name='token'),
    path('v1/recipes/<int:recipe_id>/favorite/',
         FavouriteViewSet.as_view({'delete': 'destroy', 'post': 'create'}),
         name='recipe-favorite'),
    path('v1/', include(v1_router.urls)),
]
