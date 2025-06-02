from django_filters import rest_framework as filters

from foodgram.models import Recipe


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_is_in_shopping_cart")

    class Meta:
        model = Recipe
        fields = ("author", "is_favorited", "is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            value = str(value).lower() in ("true", "1", "t", "y", "yes")
            if value:
                return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            value = str(value).lower() in ("true", "1", "t", "y", "yes")
            if value:
                return queryset.filter(in_shopping_cart__user=user)
        return queryset
