from django.core.exceptions import ValidationError

from foodgram.settings import (MIN_COOKING_TIME, MAX_COOKING_TIME,
                               MIN_AMOUNT, MAX_AMOUNT)


def cooking_time_validator(value):
    """Валидатор для времени готовки"""
    if MIN_COOKING_TIME > value or value > MAX_COOKING_TIME:
        raise ValidationError(
            f'Время готовки не должно быть меньше {MIN_COOKING_TIME} и '
            f'больше {MAX_COOKING_TIME}.'
        )


def amount_validator(value):
    """Валидатор для количества ингредиентов"""
    if MIN_AMOUNT > value or value > MAX_AMOUNT:
        raise ValidationError(
            f'Количество ингредиентов не должно быть меньше {MIN_AMOUNT} и '
            f'больше {MAX_AMOUNT}.'
        )
