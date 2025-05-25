from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Кастомная пагинация для API."""
    
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
