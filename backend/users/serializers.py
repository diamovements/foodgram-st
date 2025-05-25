from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя."""
    
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(use_url=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj: User) -> bool:
        """Проверяет, подписан ли текущий пользователь на данного пользователя."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user in obj.subscribers.all()
        return False


class UserResponseOnCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа при создании пользователя."""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class CreatePasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""
    
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class CreateAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    
    avatar = Base64ImageField(use_url=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data: dict) -> dict:
        """Проверяет, что аватар не пустой."""
        avatar = self.initial_data.get('avatar')
        if not avatar:
            raise serializers.ValidationError(_('Фото не должно быть пустым'))
        return data

