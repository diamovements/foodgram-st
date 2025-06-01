from django.urls import include, path
from rest_framework.routers import DefaultRouter

from foodgram.views import IngredientViewSet, RecipeViewSet

app_name = "foodgram"

router = DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path("", include(router.urls)),
    path("recipes/<int:pk>/get-link/", RecipeViewSet.as_view({"get": "get_link"}), name="recipe-get-link"),
]
