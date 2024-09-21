from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Recipe, Tag, Ingredient, Favourite, Cart
from .serializers import (RecipeSerializer, TokenSerializer,
                          TagSerializer, IngredientSerializer,
                          FavouriteSerializer, CartSerializer,
                          UserSerializer, FollowSerializer,
                          AvatarUserSerializer, IngredientNotAmountSerializer,
                          FollowUserSerializer, UserFollowSerializer, UserReadFollowSerializer)
from users.get_tokens_for_user import get_tokens_for_user
from users.models import Follow
from .permissions import IsAuthorOrReadOnly, IsCurrentUserOrReadOnly
from .filters import RecipeFilter
from .pagination import FollowPagination


User = get_user_model()


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        user = request.user
        recipes_limit = self.request.query_params.get('recipes_limit', None)
        queryset = User.objects.filter(respondents__user=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserReadFollowSerializer(
                page,
                many=True,
                context={'request': request,
                         'recipes_limit': recipes_limit})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AvatarUserViewSet(viewsets.ModelViewSet):
    serializer_class = AvatarUserSerializer
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
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated, IsCurrentUserOrReadOnly]
        elif self.action == 'retrieve':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('id')
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    # search_fields = ('author',)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientNotAmountSerializer
    pagination_class = None


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
    # pagination_class = FollowPagination

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
        recipes_limit = self.request.query_params.get('recipes_limit', None)
        print(type(recipes_limit))
        user_data = FollowUserSerializer(
            author, context={'request': request,
                             'recipes_limit': recipes_limit}
        ).data
        return Response(
            user_data, status=status.HTTP_201_CREATED
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        recipes_limit = self.request.query_params.get('recipes_limit', None)
        print(recipes_limit)
        if recipes_limit is not None:
            context['recipes_limit'] = int(recipes_limit)
        return context


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
    print(request.user)
    user = User.objects.filter(username=request.user).first()
    token = Token.objects.get(user=user)
    token.delete()
    return Response(token.key, status=status.HTTP_204_NO_CONTENT)


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


class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipe_detail.html'

    def get_object(self):
        short_link = self.kwargs.get('short_link')
        return get_object_or_404(Recipe, short_link=short_link)