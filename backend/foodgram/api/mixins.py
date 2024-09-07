# from .serializers import RecipeShortSerializer
# from recipes.models import Recipe


# class CreateRepresentationMixin:
#     def to_representation(self, instance):
#         recipe_data = RecipeShortSerializer(instance.recipe).data
#         return recipe_data

#     def create(self, validated_data):
#         recipe_id = (
#             self.context['request'].parser_context['kwargs']['recipe_id']
#         )
#         request = self.context.get('request')
#         recipe = Recipe.objects.get(id=recipe_id)
#         if request and hasattr(request, 'user'):
#             validated_data['author'] = request.user
#             validated_data['recipe'] = recipe
#         return super().create(validated_data)
