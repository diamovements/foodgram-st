from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .fields import Base64ImageField
from foodgram.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
from djoser.serializers import UserCreateSerializer, UserSerializer


User = get_user_model()


MIN_VALUE = 1
MAX_VALUE = 32_000


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        search_fields = ("name",)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context["request"]
            return request.build_absolute_uri(obj.avatar.url)
        return None


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        if obj.image:
            request = self.context["request"]
            return request.build_absolute_uri(obj.image.url)
        return None


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_author(self, obj):
        return CustomUserSerializer(obj.author, context=self.context).data

    def get_ingredients(self, obj):
        return RecipeIngredientSerializer(obj.recipe_ingredients.all(), many=True).data

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.favorited_by.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.in_shopping_cart.filter(user=user).exists()

    def get_image(self, obj):
        if obj.image:
            request = self.context["request"]
            return request.build_absolute_uri(obj.image.url)
        return None


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        error_messages={
            "min_value": f"Количество ингредиента должно быть не менее {MIN_VALUE}",
            "max_value": f"Количество ингредиента должно быть не более {MAX_VALUE}",
        },
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=RecipeIngredientCreateSerializer(),
        required=True,
        error_messages={"required": "Это поле обязательно."},
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        error_messages={
            "min_value": f"Время приготовления должно быть не менее {MIN_VALUE} минут",
            "max_value": f"Время приготовления должно быть не более {MAX_VALUE} минут",
        },
    )

    class Meta:
        model = Recipe
        fields = ("ingredients", "image", "name", "text", "cooking_time")

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Список ингредиентов не может быть пустым"
            )
        ingredient_ids = [item["id"] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться")
        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        if len(existing_ingredients) != len(ingredient_ids):
            raise serializers.ValidationError(
                "Один или несколько ингредиентов не существуют"
            )
        return value

    def validate(self, data):
        if not data.get("ingredients"):
            raise serializers.ValidationError({"ingredients": "Это поле обязательно."})
        return data

    def create_recipe_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient["id"],
                amount=ingredient["amount"],
            )
            for ingredient in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self.create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if "ingredients" in validated_data:
            ingredients_data = validated_data.pop("ingredients")
            instance.ingredients.clear()
            self.create_recipe_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=("user", "recipe"),
                message="Рецепт уже в избранном",
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=("user", "recipe"),
                message="Рецепт уже в списке покупок",
            )
        ]


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }


class SubscribeSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context["request"]
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        return RecipeMinifiedSerializer(
            recipes, many=True, context={"request": request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)
