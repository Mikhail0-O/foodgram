from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework import status
import re
from djoser.serializers import TokenCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import Recipe, Tag, Ingredient, Cart, Favourite
from .exceptions import CustomValidation


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)


class UserSerializer(BaseUserSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)
    email = serializers.EmailField(required=False)

    class Meta(BaseUserSerializer.Meta):
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'avatar'
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    tag = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Tag.objects.all()
    )
    ingredient = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Ingredient.objects.all()
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'is_in_shopping_cart', 'author', 'description',
                  'tag', 'ingredient', 'is_favorited', 'cooking_time')

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            cart = Cart.objects.filter(recipe=obj, author=user).first()
            if cart:
                return True
        return False

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            cart = Favourite.objects.filter(recipe=obj, author=user).first()
            if cart:
                return True
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tag'] = TagSerializer(
            instance.tag, many=True).data
        representation['ingredient'] = IngredientSerializer(
            instance.ingredient, many=True).data
        return representation
    # author = serializers.CharField(
    #     source='author.username',
    #     read_only=True
    # )


class TokenSerializer(TokenCreateSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def validate(self, data):
        username = data.get('username')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CustomValidation(
                'Не существует',
                username, status_code=status.HTTP_404_NOT_FOUND
            )

        data['user'] = user
        return data


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            # 'image',
            'cooking_time'
        )


class CreateRepresentationMixin:
    def to_representation(self, instance):
        recipe_data = RecipeShortSerializer(instance.recipe).data
        return recipe_data

    def create(self, validated_data):
        recipe_id = (
            self.context['request'].parser_context['kwargs']['recipe_id']
        )
        request = self.context.get('request')
        recipe = Recipe.objects.get(id=recipe_id)
        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user
            validated_data['recipe'] = recipe
        return super().create(validated_data)


class FavouriteSerializer(CreateRepresentationMixin,
                          serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = Favourite
        fields = ('recipe',)
        read_only_fields = ('recipe',)

    def validate(self, data):
        # Проверяем, чтобы рецепт не был уже добавлен в избранное
        recipe_id = (
            self.context['request'].parser_context['kwargs']['recipe_id']
        )
        recipe = Recipe.objects.get(id=recipe_id)
        user = self.context['request'].user
        if Favourite.objects.filter(author=user, recipe=recipe).exists():
            raise serializers.ValidationError("Этот рецепт уже в избранном.")
        return data


class CartSerializer(CreateRepresentationMixin,
                     serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ('recipe',)
        read_only_fields = ('recipe',)

    def validate(self, data):
        # Проверяем, чтобы рецепт не был уже добавлен в избранное
        recipe_id = (
            self.context['request'].parser_context['kwargs']['recipe_id']
        )
        recipe = Recipe.objects.get(id=recipe_id)
        user = self.context['request'].user
        if Cart.objects.filter(author=user, recipe=recipe).exists():
            raise serializers.ValidationError("Этот рецепт уже в избранном.")
        return data
