from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from foodgram.models import Recipe, Ingredient, Favorite, ShoppingCart, RecipeIngredient
from .serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    CustomUserSerializer,
    CustomUserCreateSerializer,
    SubscribeSerializer,
    SetPasswordSerializer,
    SetAvatarSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from users.models import Follow
from djoser.views import UserViewSet as DjoserUserViewSet


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

    @action(detail=True, methods=["post", "delete"], permission_classes=[permissions.IsAuthenticated])
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

    @action(detail=True, methods=["post", "delete"], permission_classes=[permissions.IsAuthenticated])
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

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
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


class CustomUserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        if self.action == "subscriptions":
            return SubscribeSerializer
        return CustomUserSerializer

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"current_password": ["Неверный пароль"]},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["put", "delete"], permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        if request.method == "PUT":
            if not request.data.get('avatar'):
                return Response(
                    {"avatar": ["Это поле не может быть пустым"]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SetAvatarSerializer(
                request.user, data=request.data, partial=True, context={"request": request}
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data)
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["post", "delete"], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if user == author:
                return Response({"errors": "Нельзя подписаться на самого себя"}, status=status.HTTP_400_BAD_REQUEST)
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"}, status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, author=author)
            serializer = SubscribeSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        follow = Follow.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"errors": "Вы не подписаны на этого пользователя"}, status=status.HTTP_400_BAD_REQUEST)
