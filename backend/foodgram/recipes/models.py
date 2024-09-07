from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint
from django.db.models import Q

from foodgram.settings import MAX_LEN_NAME


User = get_user_model()


class Recipe(models.Model):
    name = models.CharField('Название', max_length=MAX_LEN_NAME)
    description = models.TextField('Описание рецепта')
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    tag = models.ManyToManyField(
        'Tag',
        verbose_name='Тег',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (минуты)'
    )
    ingredient = models.ManyToManyField(
        'Ingredient',
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    image = models.ImageField('Фото', blank=True)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LEN_NAME,
        verbose_name='Название',
        unique=True
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=('Идентификатор страницы для URL; '
                   'разрешены символы латиницы, цифры, дефис и подчёркивание.')
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LEN_NAME,
        verbose_name='Название',
        unique=True
    )
    measurement_unit = models.CharField(
        max_length=MAX_LEN_NAME,
        verbose_name='Единицы измерения',
    )
    amount = models.IntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Cart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Рецепт',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Автор корзины'
    )

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'author'), name='unique_cart')
        ]

    def __str__(self):
        return f'Корзина пользователя: {self.author.username}'


class Favourite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Автор избранного'
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Список избранных рецептов'
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'author'), name='unique_favorites')
        ]

    def __str__(self):
        return f'Список избранного пользователя: {self.author.username}'
