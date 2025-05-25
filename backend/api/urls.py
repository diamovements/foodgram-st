from django.urls import include, path
from rest_framework import routers
from recipes.views import IngredientViewSet, RecipeViewSet
from .views import EditProfileAvatarView, UserViewSet

app_name = "api"

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path("", include(router.urls)),
    path("users/me/avatar/", EditProfileAvatarView.as_view(), name="avatar-update"),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
