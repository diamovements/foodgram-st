from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True)

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="Группы пользователя",
        related_name="customuser_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Права пользователя",
        related_name="customuser_user_permissions",
        related_query_name="user",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.email


class Follow(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="follower", verbose_name="Подписчик")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="following", verbose_name="Автор")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [models.UniqueConstraint(fields=["user", "author"], name="unique_follow")]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
