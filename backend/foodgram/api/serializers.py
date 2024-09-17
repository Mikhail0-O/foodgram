from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework import status
import re
from djoser.serializers import TokenCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import Recipe, Tag, Ingredient, Cart, Favourite
from users.models import Follow
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


class UserFollowSerializer(BaseUserSerializer):
    # avatar = Base64ImageField(max_length=None, use_url=True)
    email = serializers.EmailField(required=False)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = obj.user
        author = obj.author
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=author).exists()
        return False


class CustomUserCreateSerializer(BaseUserCreateSerializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'password')


class AvatarUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(BaseUserSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)
    email = serializers.EmailField(required=False)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj).exists()
        return False


class FollowSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    # author = serializers.SlugRelatedField(
    #     queryset=User.objects.all(), slug_field='id'
    # )
    # author = serializers.SerializerMethodField(required=False)
    # author = UserSerializer(required=False)
    # user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        # fields = ('author', 'recipes', 'recipes_count', 'user')
        fields = ('recipes', 'recipes_count',)
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'author'],
                message='Вы уже подписаны на этого пользователя.'
            )
        ]

    # def get_author(self, obj):
    #     return UserSerializer(obj.author).data

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.author)
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def validate(self, data):
        author_id = self.context['request'].parser_context['kwargs']['user_id']
        if self.context.get('request').user.id == author_id:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя.'
            )
        return data

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     print(representation)
    #     representation['author'] = UserFollowSerializer(instance).data

    #     # # representation['ingredient'] = IngredientSerializer(
    #     # #     instance.ingredient, many=True).data
    #     return representation


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientNotAmountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    tags = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Tag.objects.all()
    )
    ingredients = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Ingredient.objects.all()
    )
    image = Base64ImageField(max_length=None, use_url=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    description = serializers.CharField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'is_in_shopping_cart', 'author', 'description',
            'tags', 'ingredients', 'is_favorited', 'cooking_time', 'image'
        )

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
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, data):
        email = data.get('email')
        print(email)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CustomValidation(
                'Не существует',
                email, status_code=status.HTTP_404_NOT_FOUND
            )

        data['user'] = user
        return data


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
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
