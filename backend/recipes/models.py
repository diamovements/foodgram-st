from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class TimeModel(models.Model):
    """Базовая модель с полями времени создания и обновления."""
    
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        abstract = True


class IngredientModel(models.Model):
    """Модель ингредиента."""
    
    name = models.CharField(
        max_length=128,
        verbose_name=_('Название')
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name=_('Единица измерения')
    )

    class Meta:
        verbose_name = _('Ингредиент')
        verbose_name_plural = _('Ингредиенты')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class RecipeModel(TimeModel):
    """Модель рецепта."""
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('Автор')
    )
    name = models.CharField(
        max_length=256,
        verbose_name=_('Название')
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name=_('Картинка')
    )
    text = models.TextField(
        verbose_name=_('Описание')
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name=_('Время приготовления в минутах'),
        validators=[
            MinValueValidator(
                5,
                message=_('Время приготовления должно быть не менее 5 минут')
            )
        ]
    )
    ingredients = models.ManyToManyField(
        IngredientModel,
        through='RecipeIngredientModel',
        related_name='recipes',
        verbose_name=_('Ингредиенты')
    )

    class Meta:
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')
        ordering = ('-created',)

    def __str__(self) -> str:
        return self.name


class RecipeIngredientModel(models.Model):
    """Модель связи рецепта и ингредиента."""
    
    recipe = models.ForeignKey(
        RecipeModel,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name=_('Рецепт')
    )
    ingredient = models.ForeignKey(
        IngredientModel,
        on_delete=models.CASCADE,
        verbose_name=_('Ингредиент')
    )
    amount = models.PositiveIntegerField(
        verbose_name=_('Количество'),
        validators=[
            MinValueValidator(
                1,
                message=_('Количество ингредиента должно быть больше 0')
            )
        ]
    )

    class Meta:
        verbose_name = _('Ингредиент рецепта')
        verbose_name_plural = _('Ингредиенты рецепта')
        unique_together = ('recipe', 'ingredient')

    def __str__(self) -> str:
        return f'{self.ingredient.name} в {self.recipe.name} – {self.amount}'


class ShoppingCartModel(models.Model):
    """Модель списка покупок."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name=_('Пользователь')
    )
    recipe = models.ForeignKey(
        RecipeModel,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name=_('Рецепт')
    )

    class Meta:
        verbose_name = _('Список покупок')
        verbose_name_plural = _('Списки покупок')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user.username} добавил(а) {self.recipe.name} в список покупок'


class FavoriteModel(models.Model):
    """Модель избранного."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('Пользователь')
    )
    recipe = models.ForeignKey(
        RecipeModel,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('Рецепт')
    )

    class Meta:
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user.username} добавил(а) {self.recipe.name} в избранное'
