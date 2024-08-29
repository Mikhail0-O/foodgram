from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from recipes.models import Recipe
from .serializers import RecipeSerializer, TokenSerializer
from users.get_tokens_for_user import get_tokens_for_user


User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('id')
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@api_view(['POST'])
def get_token(request):
    serializer = TokenSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    user = User.objects.filter(
        username=serializer.validated_data.get('username')
    ).first()
    tokens = get_tokens_for_user(user)
    return Response(tokens, status=status.HTTP_200_OK)
