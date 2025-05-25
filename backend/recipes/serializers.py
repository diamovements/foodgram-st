from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.serializers import UserSerializer

from .models import IngredientModel, RecipeModel, RecipeIngredientModel


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиента."""
    
    id = serializers.IntegerField()
    name = serializers.CharField()
    measurement_unit = serializers.CharField()

    class Meta:
        model = IngredientModel
        fields = ('id', 'name', 'measurement_unit')


class RecipeShortenSerializer(serializers.ModelSerializer):
    """Сокращенный сериализатор для модели рецепта."""
    
    class Meta:
        model = RecipeModel
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента в рецепте."""
    
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredientModel
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateShortIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиента в рецепте."""
    
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientModel
        fields = ('id', 'amount')

    def validate_id(self, ingredient_id: int) -> int:
        """Проверка существования ингредиента."""
        try:
            IngredientModel.objects.get(id=ingredient_id)
        except IngredientModel.DoesNotExist:
            raise serializers.ValidationError(
                _('Ингредиента с id {} не существует').format(ingredient_id)
            )
        return ingredient_id

    def validate_amount(self, amount: int) -> int:
        """Проверка количества ингредиента."""
        if amount < 1:
            raise serializers.ValidationError(
                _('Количество ингредиента должно быть больше 0')
            )
        return amount


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецепта."""
    
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = RecipeModel
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, recipe: RecipeModel) -> bool:
        """Проверка наличия рецепта в избранном."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and recipe.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, recipe: RecipeModel) -> bool:
        """Проверка наличия рецепта в списке покупок."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and recipe.shopping_cart.filter(user=request.user).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""
    
    ingredients = CreateShortIngredientsSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = RecipeModel
        fields = (
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, recipe: RecipeModel) -> dict:
        """Преобразование рецепта в представление."""
        serializer = RecipeSerializer(
            recipe,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def validate(self, data: dict) -> dict:
        """Валидация данных рецепта."""
        ingredients = data.get('ingredients')
        cooking_time = data.get('cooking_time')
        image = data.get('image')

        if image is None:
            raise serializers.ValidationError({
                'image': _('Изображение обязательно')
            })
        
        if cooking_time is not None and cooking_time < 5:
            raise serializers.ValidationError(
                _('Время приготовления должно быть не менее 5 минут')
            )

        if not ingredients:
            raise serializers.ValidationError(
                _('Список ингредиентов не может быть пустым')
            )

        ingredients_id = [ingredient['id'] for ingredient in ingredients]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise serializers.ValidationError(
                _('Ингредиенты должны быть уникальными')
            )

        return data

    @transaction.atomic
    def create(self, validated_data: dict) -> RecipeModel:
        """Создание рецепта."""
        ingredients = validated_data.pop('ingredients')
        user = self.context.get('request').user
        
        recipe = RecipeModel.objects.create(
            **validated_data,
            author=user
        )
        self._create_ingredients(ingredients, recipe)
        
        return recipe

    @transaction.atomic
    def update(self, recipe: RecipeModel, validated_data: dict) -> RecipeModel:
        """Обновление рецепта."""
        RecipeIngredientModel.objects.filter(recipe=recipe).delete()
        self._create_ingredients(validated_data.pop('ingredients'), recipe)
        
        return super().update(recipe, validated_data)

    def _create_ingredients(self, ingredients: list, recipe: RecipeModel) -> None:
        """Создание связей рецепта с ингредиентами."""
        recipe_ingredients = [
            RecipeIngredientModel(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredientModel.objects.bulk_create(recipe_ingredients)
