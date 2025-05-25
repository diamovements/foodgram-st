from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from djoser.serializers import UserCreateSerializer

from users.models import User
from users.serializers import (
    CreatePasswordSerializer,
    UserSerializer,
    CreateAvatarSerializer,
)
from .pagination import CustomPagination
from .serializers import UserRecipesSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями."""
    
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор в зависимости от действия."""
        if self.action in ['list', 'retrieve', 'me']:
            return UserSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        """Изменяет пароль пользователя."""
        serializer = CreatePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'current_password': [_('Неверный пароль')]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me',
    )
    def me(self, request):
        """Возвращает информацию о текущем пользователе."""
        serializer = self.get_serializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
        url_name='subscriptions',
        pagination_class=CustomPagination,
    )
    def subscriptions(self, request):
        """Возвращает список подписок пользователя."""
        subscribed_users = request.user.subscriptions.all()
        page = self.paginate_queryset(subscribed_users)
        serializer = UserRecipesSerializer(
            page or subscribed_users,
            many=True,
            context={'request': request}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        """Обрабатывает подписку/отписку от пользователя."""
        if request.method == 'POST':
            return self.add_subscribe(request, pk)
        return self.remove_subscribe(request, pk)

    @staticmethod
    def add_subscribe(request, pk=None):
        """Добавляет подписку на пользователя."""
        try:
            user = request.user
            author = get_object_or_404(User, pk=pk)

            if user == author:
                return Response(
                    {'errors': _('Запрещено подписываться на свой аккаунт')},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.subscriptions.filter(pk=author.pk).exists():
                return Response(
                    {'errors': _('Вы уже подписаны')},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.subscriptions.add(author)
            serializer = UserRecipesSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception:
            return Response(
                {'detail': _('Произошла ошибка при подписке')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def remove_subscribe(request, pk=None):
        """Удаляет подписку на пользователя."""
        try:
            author = get_object_or_404(User, pk=pk)
            
            if not request.user.subscriptions.filter(pk=author.pk).exists():
                return Response(
                    {'detail': _('Вы не подписаны на {}').format(author.username)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            request.user.subscriptions.remove(author)
            return Response(
                {'detail': _('Вы отписались от {}').format(author.username)},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception:
            return Response(
                {'detail': _('Произошла ошибка при отписке')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EditProfileAvatarView(APIView):
    """Представление для редактирования аватара пользователя."""
    
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """Обновляет аватар пользователя."""
        serializer = CreateAvatarSerializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def delete(self, request, *args, **kwargs):
        """Удаляет аватар пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request):
        """Частично обновляет аватар пользователя."""
        return self.put(request)