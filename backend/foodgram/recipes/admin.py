from django.contrib import admin

from .models import Recipe, Tag, Ingredient, Cart, Favourite


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'description', 'tag_list',
        'ingredient_list',
    )
    # search_fields = ('name', 'year', 'category__name')
    # list_filter = ('year', 'category', 'genre')
    list_editable = ('name', 'description',)

    def tag_list(self, obj):
        return ", ".join(obj.tag.values_list('name', flat=True))

    tag_list.short_description = 'Теги'

    def ingredient_list(self, obj):
        return ", ".join(obj.ingredient.values_list('name', flat=True))

    ingredient_list.short_description = 'Список ингредиентов'

    # def tag_list(self, obj):
    #     return ", ".join([str(item) for item in obj.many_to_many_field.all()])
    # tag_list.short_description = 'Related Items'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',)


class CartAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')

    # def recipe_list(self, obj):
    #     return ", ".join(obj.recipe.values_list('name', flat=True))

    # recipe_list.short_description = 'Список рецептов'


class FavouritesAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')

    # def recipe_list(self, obj):
    #     return ", ".join(obj.recipe.values_list('name', flat=True))

    # recipe_list.short_description = 'Список рецептов в избранном'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Favourite, FavouritesAdmin)
