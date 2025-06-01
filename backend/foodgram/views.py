from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Recipe, Ingredient, Favorite, ShoppingCart, RecipeIngredient
from .serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from foodgram.filters import RecipeFilter
from foodgram.permissions import IsAuthorOrReadOnly
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return RecipeCreateSerializer
        if self.action in ("favorite", "shopping_cart", "get_link"):
            return RecipeMinifiedSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = RecipeSerializer(serializer.instance, context={"request": request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = RecipeSerializer(serializer.instance, context={"request": request})
        return Response(read_serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def get_queryset(self):
        return Recipe.objects.all()

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({"errors": "Рецепт уже в избранном"}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        fav = Favorite.objects.filter(user=user, recipe=recipe)
        if fav.exists():
            fav.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"errors": "Рецепта не было в избранном"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({"errors": "Рецепт уже в корзине"}, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if cart.exists():
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"errors": "Рецепта не было в корзине"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = {}
        cart_items = ShoppingCart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"errors": "Ваш список покупок пуст"}, status=status.HTTP_400_BAD_REQUEST)
        for item in cart_items:
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=item.recipe)
            for recipe_ing in recipe_ingredients:
                ing = recipe_ing.ingredient
                amount = recipe_ing.amount
                if ing.id in ingredients:
                    ingredients[ing.id]["amount"] += amount
                else:
                    ingredients[ing.id] = {"name": ing.name,
                                           "measurement_unit": ing.measurement_unit,
                                           "amount": amount}

        shopping_list = ["Список покупок:\n"]
        sorted_ingredients = sorted(ingredients.values(), key=lambda x: x["name"].lower())

        for ingredient in sorted_ingredients:
            shopping_list.append(
                f'{ingredient["name"]} ({ingredient["measurement_unit"]}) — ' f'{ingredient["amount"]}\n'
            )

        response = Response(shopping_list)
        response["Content-Type"] = "text/plain"
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        url = f"http://{request.get_host()}/recipes/{recipe.id}/"
        return Response({"short-link": url})


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset
