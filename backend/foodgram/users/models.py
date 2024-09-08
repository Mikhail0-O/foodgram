from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator
from django.db.models import UniqueConstraint

from foodgram.settings import VALID_USERNAME_CHARACTERS
from .validators import validate_username


class CustomUser(AbstractUser):
    username = models.CharField(
        'username', max_length=150, unique=True,
        validators=[validate_username,
                    MinLengthValidator(limit_value=5),
                    RegexValidator(regex=VALID_USERNAME_CHARACTERS)]
    )
    email = models.EmailField(
        'email',
        unique=True, max_length=254)
    avatar = models.ImageField('Аватар', blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    author = models.ForeignKey(
        CustomUser,
        related_name='respondents',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )

    user = models.ForeignKey(
        CustomUser,
        related_name='followers',
        on_delete=models.CASCADE,
        verbose_name='Фоловер'
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'author'],
                             name='unique_follow')
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
