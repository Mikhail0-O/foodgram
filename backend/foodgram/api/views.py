from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from recipes.models import Recipe, Tag, Ingredient, Favourite
from .serializers import RecipeSerializer, TokenSerializer, TagSerializer, IngredientSerializer, RecipeShortSerializer, FavouriteSerializer
from users.get_tokens_for_user import get_tokens_for_user
from .permissions import IsAuthorOrReadOnly


User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('id')
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientSerializer


class FavouriteViewSet(viewsets.ModelViewSet):
    queryset = Favourite.objects.all().order_by('id')
    serializer_class = FavouriteSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        try:
            favourite = Favourite.objects.get(
                recipe_id=recipe_id, author=request.user
            )
            favourite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Favourite.DoesNotExist:
            return Response(
                {'detail': 'Избранное не найдено.'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = User.objects.filter(
        username=serializer.validated_data.get('username')
    ).first()
    tokens = get_tokens_for_user(user)
    return Response(tokens, status=status.HTTP_200_OK)
