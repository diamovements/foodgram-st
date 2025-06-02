from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

MIN_VALUE = 1
MAX_VALUE = 32_000


class Ingredient(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    measurement_unit = models.CharField(
        max_length=200, verbose_name="Единица измерения"
    )

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "measurement_unit")
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", verbose_name="Автор"
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(upload_to="foodgram/images/", verbose_name="Изображение")
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", verbose_name="Ингредиенты"
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message=f"Время приготовления должно быть не менее {MIN_VALUE} минут",
            ),
            MaxValueValidator(
                MAX_VALUE,
                message=f"Время приготовления должно быть не более {MAX_VALUE} минут",
            ),
        ],
        verbose_name="Время приготовления в минутах",
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message=f"Количество ингредиента должно быть не менее {MIN_VALUE}",
            ),
            MaxValueValidator(
                MAX_VALUE,
                message=f"Количество ингредиента должно быть не более {MAX_VALUE}",
            ),
        ],
        verbose_name="Количество",
    )

    class Meta:
        ordering = ["recipe", "ingredient"]
        unique_together = ("recipe", "ingredient")
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"

    def __str__(self):
        return (
            f"{self.ingredient.name} - {self.amount} {self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Рецепт",
    )

    class Meta:
        ordering = ["-recipe__pub_date"]
        unique_together = ("user", "recipe")
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        ordering = ["-recipe__pub_date"]
        unique_together = ("user", "recipe")
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
