from django.contrib import admin

from .models import (Cart, Favourite, Ingredient, IngredientForRecipe, Recipe,
                     Tag)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'text', 'tag_list',
        'ingredient_list',
    )
    list_editable = ('name', 'text',)

    def tag_list(self, obj):
        return ", ".join(obj.tags.values_list('name', flat=True))

    tag_list.short_description = 'Теги'

    def ingredient_list(self, obj):
        return (", ".join(
            obj.ingredients.values_list('ingredient__name', flat=True)))

    ingredient_list.short_description = 'Список ингредиентов'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',)


class IngredientForRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'ingredient',
        'amount',
    )


class CartAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')


class FavouritesAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientForRecipe, IngredientForRecipeAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Favourite, FavouritesAdmin)
