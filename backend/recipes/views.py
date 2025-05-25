from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from api.pagination import CustomPagination
from api.permissions import CanEditOrNot
from .filters import IngredientModelFilter, RecipeModelFilter
from .models import IngredientModel, RecipeModel, RecipeIngredientModel
from .serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeShortenSerializer,
    RecipeSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с ингредиентами."""
    
    queryset = IngredientModel.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientModelFilter
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для работы с рецептами."""
    
    queryset = RecipeModel.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeModelFilter
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly, CanEditOrNot)

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода запроса."""
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(IsAuthenticatedOrReadOnly,),
        url_path='get-link',
        url_name='get-link',
    )
    def get_short_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(RecipeModel, pk=pk)
        short_link = '{}/recipes/{}'.format(request.get_host(), recipe.id)
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request):
        """Получение списка покупок пользователя."""
        recipes = RecipeModel.objects.filter(shopping_cart__user=request.user)
        page = self.paginate_queryset(recipes)
        serializer = RecipeShortenSerializer(
            page or recipes,
            many=True,
            context={'request': request}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в текстовом формате."""
        ingredients = (
            RecipeIngredientModel.objects.filter(
                recipe__shopping_cart__user=request.user
            )
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit'),
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('name')
        )

        shopping_list = [
            '{} ({}) — {}\n'.format(
                item['name'],
                item['unit'],
                item['total_amount']
            )
            for item in ingredients
        ]
        content = ''.join(shopping_list)
        return Response(content, content_type='text/plain')

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart_change(self, request, pk=None):
        """Добавление/удаление рецепта из списка покупок."""
        if request.method == 'POST':
            return self._add_to_shopping_cart(request, pk)
        return self._remove_from_shopping_cart(request, pk)

    @staticmethod
    def _remove_from_shopping_cart(request, pk=None):
        """Удаление рецепта из списка покупок."""
        recipe = get_object_or_404(RecipeModel, pk=pk)
        user = request.user
        
        if not recipe.shopping_cart.filter(user=user).exists():
            return Response(
                {'errors': _('Рецепта нет в корзине')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        recipe.shopping_cart.filter(user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _add_to_shopping_cart(request, pk=None):
        """Добавление рецепта в список покупок."""
        recipe = get_object_or_404(RecipeModel, pk=pk)
        user = request.user
        
        if recipe.shopping_cart.filter(user=user).exists():
            return Response(
                {'errors': _('Рецепт уже в корзине')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        recipe.shopping_cart.create(user=user)
        data = RecipeShortenSerializer(
            recipe,
            context={'request': request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def list_favorites(self, request):
        """Получение списка избранных рецептов."""
        favorites = RecipeModel.objects.filter(favorites__user=request.user)
        page = self.paginate_queryset(favorites)
        serializer = RecipeShortenSerializer(
            page or favorites,
            many=True,
            context={'request': request}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта из избранного."""
        if request.method == 'POST':
            return self._add_to_favorite(request, pk)
        return self._remove_from_favorite(request, pk)

    @staticmethod
    def _add_to_favorite(request, pk=None):
        """Добавление рецепта в избранное."""
        recipe = get_object_or_404(RecipeModel, pk=pk)
        
        if recipe.favorites.filter(user=request.user).exists():
            return Response(
                {'errors': _('Рецепт уже в избранном')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        recipe.favorites.create(user=request.user)
        data = RecipeShortenSerializer(
            recipe,
            context={'request': request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _remove_from_favorite(request, pk=None):
        """Удаление рецепта из избранного."""
        recipe = get_object_or_404(RecipeModel, pk=pk)
        
        if not recipe.favorites.filter(user=request.user).exists():
            return Response(
                {'errors': _('Рецепта нет в избранном')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        recipe.favorites.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
