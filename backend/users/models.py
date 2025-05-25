from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Модель пользователя."""
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        verbose_name=_('Электронная почта'),
        max_length=254,
        unique=True,
    )
    username = models.CharField(
        verbose_name=_('Имя пользователя'),
        max_length=50,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=_('Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_')
            )
        ],
    )
    first_name = models.CharField(
        verbose_name=_('Имя'),
        max_length=50,
    )
    last_name = models.CharField(
        verbose_name=_('Фамилия'),
        max_length=50,
    )
    avatar = models.ImageField(
        verbose_name=_('Аватар пользователя'),
        upload_to='users/avatars/',
        blank=True,
    )
    subscriptions = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='subscribers',
        blank=True,
        verbose_name=_('Подписки'),
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ('username',)

    def __str__(self) -> str:
        return self.username
