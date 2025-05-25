from rest_framework import permissions


class CanEditOrNot(permissions.BasePermission):
    """Разрешение для проверки прав на редактирование объекта."""
    
    def has_object_permission(self, request, view, obj):
        """
        Проверяет, имеет ли пользователь право на редактирование объекта.
        
        Args:
            request: HTTP запрос
            view: Представление
            obj: Объект для проверки прав
            
        Returns:
            bool: True если пользователь имеет право на редактирование,
                 False в противном случае
        """
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )