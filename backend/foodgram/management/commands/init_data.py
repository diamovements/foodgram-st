import json
import os
from django.core.management.base import BaseCommand
from foodgram.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка ингредиентов из JSON файла"

    def handle(self, *args, **options):
        try:
            file_path = "/app/data/ingredients.json"
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
                return

            with open(file_path, "r", encoding="utf-8") as file:
                ingredients = json.load(file)

            self.stdout.write(f"Найдено {len(ingredients)} ингредиентов для загрузки")

            for ingredient in ingredients:
                Ingredient.objects.get_or_create(
                    name=ingredient["name"],
                    measurement_unit=ingredient["measurement_unit"],
                )

            self.stdout.write(self.style.SUCCESS("Все ингредиенты загружены"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {str(e)}"))
            import traceback

            self.stdout.write(traceback.format_exc())
