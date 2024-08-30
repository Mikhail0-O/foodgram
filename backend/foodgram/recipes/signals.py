from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cart, Favourites


User = get_user_model()


@receiver(post_save, sender=User)
def create_cart_and_favorite(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(author=instance)
        Favourites.objects.create(author=instance)
