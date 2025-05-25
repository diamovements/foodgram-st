from rest_framework import serializers
from recipes.serializers import RecipeShortenSerializer
from users.models import User


class UserRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с его рецептами."""
    
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj: User) -> list:
        """
        Получает список рецептов пользователя.
        
        Args:
            obj: Пользователь
            
        Returns:
            list: Список рецептов пользователя
        """
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        
        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]
            
        return RecipeShortenSerializer(queryset, many=True).data

    def get_is_subscribed(self, obj: User) -> bool:
        """
        Проверяет, подписан ли текущий пользователь на данного пользователя.
        
        Args:
            obj: Пользователь
            
        Returns:
            bool: True если пользователь подписан, False в противном случае
        """
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and obj in request.user.subscriptions.all()
        )

    @staticmethod
    def get_recipes_count(obj: User) -> int:
        """
        Получает количество рецептов пользователя.
        
        Args:
            obj: Пользователь
            
        Returns:
            int: Количество рецептов пользователя
        """
        return obj.recipes.count()
