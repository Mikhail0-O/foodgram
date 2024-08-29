from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework import status
import re

from recipes.models import Recipe, Tag, Ingredient, Cart, Favourites
from .exceptions import CustomValidation


User = get_user_model()


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
        # fields = '__all__'
        fields = ('id', 'name', 'is_in_shopping_cart', 'author',
                  'tag', 'ingredient', 'is_favorited')

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
            cart = Favourites.objects.filter(recipe=obj, author=user).first()
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


class TokenSerializer(serializers.Serializer):
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
