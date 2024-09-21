from rest_framework.pagination import LimitOffsetPagination


class FollowPagination(LimitOffsetPagination):
    page_size_query_param = 'recipes_limit'
