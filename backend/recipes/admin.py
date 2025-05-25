from django.contrib import admin
from django.contrib.admin import register

from recipes.models import FavoriteModel, IngredientModel, RecipeModel, RecipeIngredientModel, ShoppingCartModel


@register(ShoppingCartModel)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    list_filter = ("user", "recipe")
    

@register(RecipeModel)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "author", "favorites_count")
    search_fields = ("name", "author__username", "author__email")

    @admin.display(description="Добавлено в избранное раз")
    def favorites_count(self, obj):
        return obj.favorites.count()


@register(IngredientModel)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    search_fields = ("name",)


@register(FavoriteModel)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    list_filter = ("user", "recipe")


@register(RecipeIngredientModel)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "ingredient", "amount")
    list_filter = ("recipe", "ingredient")

