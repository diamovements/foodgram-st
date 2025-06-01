from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Recipe, Ingredient, RecipeIngredient, Favorite, ShoppingCart
from django.contrib.auth import get_user_model


User = get_user_model()


class RecipeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.ingredient = Ingredient.objects.create(name="яблоки", measurement_unit="г")

    def test_create_recipe(self):
        recipe = Recipe.objects.create(author=self.user, name="Тестовый рецепт", text="Описание", cooking_time=10)
        self.assertEqual(recipe.name, "Тестовый рецепт")
        self.assertEqual(recipe.author, self.user)

    def test_create_recipe_with_ingredients(self):
        recipe = Recipe.objects.create(author=self.user, name="Тестовый рецепт", text="Описание", cooking_time=10)
        recipe_ingredient = RecipeIngredient.objects.create(recipe=recipe, ingredient=self.ingredient, amount=100)
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertEqual(recipe_ingredient.amount, 100)


class IngredientAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Ingredient.objects.create(name="яблоки", measurement_unit="г")
        Ingredient.objects.create(name="груши", measurement_unit="г")

    def test_list_ingredients(self):
        url = reverse("foodgram:ingredients-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_search_ingredients(self):
        url = reverse("foodgram:ingredients-list")
        response = self.client.get(url + "?name=яблоки")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "яблоки")


class RecipeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="recipeuser", password="recipepass")
        self.client.force_authenticate(user=self.user)
        self.ingredient = Ingredient.objects.create(name="Тестовый ингредиент", measurement_unit="г")
        self.recipe_data = {
            "name": "Тестовый рецепт",
            "text": "Описание рецепта",
            "cooking_time": 30,
            "ingredients": [{"id": self.ingredient.id, "amount": 100}],
            "image": (
                "data:image/png;base64,"
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
            )
        }

    def test_create_recipe(self):
        url = reverse("foodgram:recipes-list")
        response = self.client.post(url, self.recipe_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(Recipe.objects.first().name, "Тестовый рецепт")

    def test_create_recipe_without_ingredients(self):
        url = reverse("foodgram:recipes-list")
        data = self.recipe_data.copy()
        data.pop("ingredients")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_ingredient(self):
        url = reverse("foodgram:recipes-list")
        data = self.recipe_data.copy()
        data["ingredients"] = [{"id": 999, "amount": 100}]
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe(self):
        recipe = Recipe.objects.create(
            author=self.user,
            name="Старый рецепт",
            text="Старое описание",
            cooking_time=20
        )
        RecipeIngredient.objects.create(recipe=recipe, ingredient=self.ingredient, amount=50)
        url = reverse("foodgram:recipes-detail", args=[recipe.id])
        update_data = {
            "name": "Обновленный рецепт",
            "text": "Новое описание",
            "cooking_time": 40,
            "ingredients": [{"id": self.ingredient.id, "amount": 200}]
        }
        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.name, "Обновленный рецепт")
        updated_ingredient = RecipeIngredient.objects.get(recipe=recipe, ingredient=self.ingredient)
        self.assertEqual(updated_ingredient.amount, 200)

    def test_update_recipe_without_ingredients(self):
        recipe = Recipe.objects.create(
            author=self.user,
            name="Тестовый рецепт",
            text="Описание",
            cooking_time=20
        )
        url = reverse("foodgram:recipes-detail", args=[recipe.id])
        update_data = {
            "name": "Обновленный рецепт",
            "text": "Новое описание",
            "cooking_time": 40
        }
        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_recipe(self):
        recipe = Recipe.objects.create(
            author=self.user,
            name="Тестовый рецепт",
            text="Описание",
            cooking_time=20
        )
        url = reverse("foodgram:recipes-detail", args=[recipe.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.count(), 0)


class FavoriteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="favuser", password="favpass")
        self.client.force_authenticate(user=self.user)
        self.recipe = Recipe.objects.create(
            author=self.user,
            name="Любимый рецепт",
            text="Описание",
            cooking_time=5
        )

    def test_add_favorite(self):
        url = reverse("foodgram:recipes-favorite", args=[self.recipe.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Favorite.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_add_favorite_twice(self):
        url = reverse("foodgram:recipes-favorite", args=[self.recipe.id])
        self.client.post(url)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_favorite(self):
        Favorite.objects.create(user=self.user, recipe=self.recipe)
        url = reverse("foodgram:recipes-favorite", args=[self.recipe.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(user=self.user, recipe=self.recipe).exists())


class ShoppingCartAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="cartuser", password="cartpass")
        self.client.force_authenticate(user=self.user)
        self.recipe = Recipe.objects.create(
            author=self.user,
            name="Рецепт для списка покупок",
            text="Описание",
            cooking_time=15
        )

    def test_add_to_shopping_cart(self):
        url = reverse("foodgram:recipes-shopping-cart", args=[self.recipe.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ShoppingCart.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_add_to_shopping_cart_twice(self):
        url = reverse("foodgram:recipes-shopping-cart", args=[self.recipe.id])
        self.client.post(url)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_from_shopping_cart(self):
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        url = reverse("foodgram:recipes-shopping-cart", args=[self.recipe.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShoppingCart.objects.filter(user=self.user, recipe=self.recipe).exists())
