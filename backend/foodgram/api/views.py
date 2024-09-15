from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from djoser.views import UserViewSet as BaseUserViewSet

from recipes.models import Recipe, Tag, Ingredient, Favourite, Cart
from .serializers import (RecipeSerializer, TokenSerializer,
                          TagSerializer, IngredientSerializer,
                          FavouriteSerializer, CartSerializer,
                          UserSerializer, FollowSerializer)
from users.get_tokens_for_user import get_tokens_for_user
from users.models import Follow
from .permissions import IsAuthorOrReadOnly


User = get_user_model()


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)


class AvatarUserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all().order_by('id')

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(BaseUserViewSet):
    serializer_class = UserSerializer


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


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all().order_by('id')
    serializer_class = CartSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        try:
            favourite = Cart.objects.get(
                recipe_id=recipe_id, author=request.user
            )
            favourite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response(
                {'detail': 'Корзина не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class FollowDestroyUpdateViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all().order_by('id')
    serializer_class = FollowSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        author = User.objects.filter(id=user_id).first()
        try:
            follow = Follow.objects.get(
                author=author, user=request.user
            )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            return Response(
                {'detail': 'Подписка не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        author = get_object_or_404(User, id=user_id)
        # data = {
        #     'author': author.id,
        #     'user': request.user.id
        # }
        data = {}
        user_data = UserSerializer(author, context={'request': request}).data
        # data.update(user_data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # print(serializer.data)
        user_data.update(serializer.data)
        user_data.popitem('author')
        # user_data.popitem('user')
        return Response(
            user_data, status=status.HTTP_201_CREATED, headers=headers
        )


# @api_view(['POST'])
# def get_token(request):
#     serializer = TokenSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     username = serializer.validated_data.get('username')
#     user = User.objects.filter(username=username).first()
#     if not user:
#         return Response({'detail': f'Пользователь {username} не существует.'},
#                         status=status.HTTP_404_NOT_FOUND)
#     token, created = Token.objects.get_or_create(user=user)
#     return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


@api_view(['POST'])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data.get('email')
    user = User.objects.filter(email=email).first()
    if not user:
        return Response({'detail': f'Пользователь {email} не существует.'},
                        status=status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user)
    return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


@api_view(['POST'])
def delete_token(request):
    user = User.objects.filter(username=request.user).first()
    token = Token.objects.get(user=user)
    token.delete()
    return Response({'detail': token.key}, status=status.HTTP_200_OK)


@api_view(['GET'])
def download_shopping_cart(request):
    user = request.user
    if not user.carts.exists():
        return Response(status=status.HTTP_400_BAD_REQUEST)
    ingredients = user.carts.all().values(
        'recipe__ingredient__measurement_unit',
        'recipe__ingredient__name'
    ).annotate(
        amount=Sum('recipe__ingredient__amount')
    ).order_by('recipe__ingredient__measurement_unit')
    shopping_cart_list = []
    shopping_cart_list += '\n'.join([
        f'- {ingredient["recipe__ingredient__name"]} '
        f'— {ingredient["amount"]} '
        f'{ingredient["recipe__ingredient__measurement_unit"]}'
        for ingredient in ingredients
    ])
    response = HttpResponse(
        shopping_cart_list, content_type='text.txt; charset=utf-8'
    )
    filename = 'shopping_cart_list.txt'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
