from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import CustomUserViewSet

app_name = "users"

router = DefaultRouter()
router.register("users", CustomUserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("users/set_password/", CustomUserViewSet.as_view({"post": "set_password"}), name="set_password"),
    path("users/me/avatar/", CustomUserViewSet.as_view({"put": "avatar", "delete": "avatar"}), name="avatar"),
    path("users/subscriptions/", CustomUserViewSet.as_view({"get": "subscriptions"}), name="subscriptions"),
    path(
        "users/<int:id>/subscribe/",
        CustomUserViewSet.as_view({"post": "subscribe", "delete": "subscribe"}),
        name="subscribe",
    ),
]
