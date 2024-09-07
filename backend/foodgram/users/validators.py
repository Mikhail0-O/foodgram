from django.core.exceptions import ValidationError


def validate_username(value):
    if value == 'me':
        raise ValidationError(
            f"Использовать имя '{value}' в качестве username запрещено"
        )
