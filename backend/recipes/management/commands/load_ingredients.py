import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand
from recipes.models import IngredientModel


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON файла'

    def _get_ingredients_file_path(self) -> Path:
        """Получение абсолютного пути к файлу с ингредиентами."""
        current_dir = Path(__file__).parent
        return current_dir.parent.parent.parent / 'data' / 'ingredients.json'

    def _load_ingredients_data(self, file_path: Path) -> list:
        """Загрузка данных из JSON файла."""
        with open(file_path, encoding='utf-8') as file:
            return json.load(file)

    def _save_ingredients(self, ingredients_data: list) -> int:
        """Сохранение ингредиентов в базу данных."""
        saved_count = 0
        for ingredient in ingredients_data:
            _, created = IngredientModel.objects.get_or_create(**ingredient)
            if created:
                saved_count += 1
        return saved_count

    def handle(self, *args, **options):
        try:
            file_path = self._get_ingredients_file_path()
            ingredients_data = self._load_ingredients_data(file_path)
            saved_count = self._save_ingredients(ingredients_data)
            
            self.stdout.write(
                self.style.SUCCESS(f'Успешно загружено {saved_count} ингредиентов')
            )
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(f'Файл не найден: {file_path}')
            )
        except Exception as error:
            self.stderr.write(
                self.style.ERROR(f'Ошибка при загрузке ингредиентов: {error}')
            )
