import django_filters
from django_filters import rest_framework as filters
from .models import IngredientModel, RecipeModel


class IngredientModelFilter(filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = IngredientModel
        fields = ("name",)


class RecipeModelFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method="filter_favs")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_cart")

    def filter_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not value or not (user and user.is_authenticated):
            return queryset
        if value:
            if not (user and user.is_authenticated):
                return queryset.none()
            return queryset.filter(shopping_cart__user=user)
        return queryset.exclude(shopping_cart__user=user)
    
    
    def filter_favs(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not value or not (user and user.is_authenticated):
            return queryset
        if value:
            if not (user and user.is_authenticated):
                return queryset.none()
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)

    class Meta:
        model = RecipeModel
        fields = (
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )
