import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import TokenCreateSerializer
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers, status

from recipes.models import (Cart, Favourite, Ingredient, IngredientForRecipe,
                            Recipe, Tag)
from users.models import Follow
from .exceptions import CustomValidation
from foodgram.settings import (MIN_AMOUNT, MAX_AMOUNT,
                               MAX_COOKING_TIME, MIN_COOKING_TIME)


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
            return user.followers.filter(author=author).exists()
        return False


class UserReadFollowSerializer(BaseUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(max_length=None, use_url=True)
    email = serializers.EmailField(required=False)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'is_subscribed', 'avatar', 'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        author = obj
        if user.is_authenticated:
            return user.followers.filter(author=author).exists()
        return False

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipes_limit = self.context.get('recipes_limit', None)

        if recipes_limit:
            representation['recipes'] = (representation['recipes']
                                         [:int(recipes_limit)])
        return representation


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
        user = self.context['request'].user
        if user.is_authenticated:
            return user.followers.filter(author=obj).exists()
        return False


class FollowUserSerializer(BaseUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(max_length=None, use_url=True)
    email = serializers.EmailField(required=False)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'avatar', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user == obj:
            raise serializers.ValidationError(
                {'detail': 'Вы не можете подписаться на самого себя.'}
            )
        if user.is_authenticated:
            if user.followers.filter(author=obj).exists():
                raise serializers.ValidationError(
                    {'obj': 'Вы уже подписаны на этого пользователя.'}
                )
            Follow.objects.create(user=user, author=obj)
            return user.followers.filter(author=obj).exists()
        return False

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipes_limit = self.context.get('recipes_limit', None)

        if recipes_limit:
            representation['recipes'] = (representation['recipes']
                                         [:int(recipes_limit)])
        return representation


class UserReadSerializer(BaseUserSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)
    email = serializers.EmailField(required=False)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.followers.filter(author=obj).exists()
        return False


class FollowSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = ('recipes', 'recipes_count',)
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'author'],
                message='Вы уже подписаны на этого пользователя.'
            )
        ]

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()

    def validate(self, data):
        author_id = self.context['request'].parser_context['kwargs']['user_id']
        if self.context['request'].user.id == author_id:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя.'
            )
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipes_limit = self.context.get('recipes_limit', None)
        if recipes_limit:
            representation['recipes'] = (representation['recipes']
                                         [:recipes_limit])
        return representation


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientNotAmountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientForCreateRecipe(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT, max_value=MAX_AMOUNT
    )

    class Meta:
        model = IngredientForRecipe
        fields = ('id', 'amount')


class IngredientReadSerilizer(serializers.ModelSerializer):

    id = serializers.IntegerField(
        source='ingredient.id', read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name', read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientForRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientReadSerilizer(many=True, read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'text', 'tags', 'ingredients',
            'is_in_shopping_cart', 'is_favorited', 'cooking_time', 'image'
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            cart = user.carts.filter(recipe=obj).exists()
            if cart:
                return True
        return False

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            cart = user.favorites.filter(recipe=obj).exists()
            if cart:
                return True
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )
    ingredients = IngredientForCreateRecipe(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'text', 'tags', 'ingredients',
            'cooking_time', 'image'
        )

    def create_ingredients(self, recipe, ingredients_data):
        ingredient_instances = []
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data['id'].id
            )
            ingredient_instance = IngredientForRecipe(
                ingredient=ingredient,
                amount=ingredient_data['amount'],
            )
            ingredient_instances.append(ingredient_instance)
        IngredientForRecipe.objects.bulk_create(ingredient_instances)

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                {'ingredients': 'Поле не может быть пустым'}
            )
        ingredients = [ingredient['id'] for ingredient in value]
        if len(set(ingredients)) != len(ingredients):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не могут повторяться'}
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                {'tags': 'Поле не может быть пустым'}
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                {'tags': 'Теги не могут повторяться'}
            )
        return value

    def validate(self, data):
        if not data.get('text'):
            raise serializers.ValidationError(
                {'text': 'Отсутствует поле'}
            )
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                {'ingredients': 'Отсутствует поле'}
            )
        if not data.get('tags'):
            raise serializers.ValidationError(
                {'tags': 'Отсутствует поле'}
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance, context=context).data


class TokenSerializer(TokenCreateSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, data):
        email = data.get('email')
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
        recipe_id = (
            self.context['request'].parser_context['kwargs']['recipe_id']
        )
        recipe = get_object_or_404(Recipe.objects.filter(id=recipe_id))
        user = self.context['request'].user
        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Этот рецепт уже в избранном.')
        return data


class CartSerializer(CreateRepresentationMixin,
                     serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ('recipe',)
        read_only_fields = ('recipe',)

    def validate(self, data):
        recipe_id = (
            self.context['request'].parser_context['kwargs']['recipe_id']
        )
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.context['request'].user
        if user.carts.filter(recipe=recipe).exists():
            raise serializers.ValidationError("Этот рецепт уже в избранном.")
        return data


class RecipeLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['short_link']

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/r/{obj.short_link}/')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_link')
        return representation
