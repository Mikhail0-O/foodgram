from django.shortcuts import render
from django.views.generic import ListView

from .models import Recipe


class PostListView(ListView):
    model = Recipe
    template_name = 'blog/index.html'

    def get_queryset(self):
        queryset = posts_query_set().filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
        return queryset
