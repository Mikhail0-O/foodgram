from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status, views, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from recipes.models import Cart, Favourite, Ingredient, Recipe, Tag
from .pagination import RecipePagination
from users.models import Follow
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly, IsCurrentUserOrReadOnly
from .serializers import (AvatarUserSerializer, CartSerializer,
                          FavouriteSerializer, FollowSerializer,
                          FollowUserSerializer, IngredientNotAmountSerializer,
                          RecipeLinkSerializer,
                          TagSerializer, TokenSerializer,
                          UserReadFollowSerializer, UserSerializer,
                          RecipeReadSerializer, RecipeCreateUpdateSerializer)


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
    queryset = User.objects.all()

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
            self.permission_classes = [IsAuthenticated,
                                       IsCurrentUserOrReadOnly]
        elif self.action == 'retrieve':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientNotAmountSerializer
    pagination_class = None


class FavouriteViewSet(viewsets.ModelViewSet):
    queryset = Favourite.objects.all()
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
    queryset = Cart.objects.all()
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
    queryset = Follow.objects.all()
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
        recipes_limit = self.request.query_params.get('recipes_limit', None)
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
    user = request.user
    token = Token.objects.get(user=user)
    token.delete()
    return Response(token.key, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def download_shopping_cart(request):
    user = request.user
    if not user.carts.exists():
        return Response(status=status.HTTP_400_BAD_REQUEST)
    ingredients = user.carts.all().values(
        'recipe__ingredients__ingredient__measurement_unit',
        'recipe__ingredients__ingredient__name'
    ).annotate(
        amount=Sum('recipe__ingredients__amount')
    ).order_by('recipe__ingredients__ingredient__measurement_unit')
    shopping_cart_list = []
    shopping_cart_list += '\n'.join([
        f'- {ingredient["recipe__ingredients__ingredient__name"]} '
        f'— {ingredient["amount"]} '
        f'{ingredient["recipe__ingredients__ingredient__measurement_unit"]}'
        for ingredient in ingredients
    ])
    response = HttpResponse(
        shopping_cart_list, content_type='text.txt; charset=utf-8'
    )
    filename = 'shopping_cart_list.txt'
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


class RecipeLinkView(views.APIView):

    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        serializer = RecipeLinkSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
