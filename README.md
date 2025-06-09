# Итоговый проект *Яндекс.Практикум - Бэкенд-разработка* - FoodGram


Веб-приложение Foodgram является кулинарным аналогом социальной сети и позволяет хранить, создавать и делиться рецептами с другими пользователями, а также составлять список покупок по рецепту.

## Стэк проекта
- Язык программирования Python
- Фреймворк Django & Django REST Framework & Djoser
- СУБД SQLite & PostgreSQL
- HTTP-сервер для Python Gunicorn
- Веб-сервер Nginx
- Контейнеризация Docker & Docker Compose
- Фронтенд React
- Воркфлоу GitHub Actions

## Запуск проекта

### Локально, бэкенд-часть

1. Склонируйте репозиторий и перейдите в папку backend

2. Создайте виртуальное окружение и активируйт его командами
``` bash
    python -m venv venv
    source venv/bin/activate
```

3. Установите зависимости из файла requirements.txt
``` bash
    pip install --upgrade pip
    pip install -r requirements.txt
```

4. Примените миграции и загрузите ингредиенты
``` bash
    python manage.py makemigrations
    python manage.py migrate
    python manage.py init_data
```

6. Соберите статику
``` bash
    python manage.py collectstatic --noinput
```

7. Запустите командой
``` bash
    python manage.py runserver
```

8. Откройте проект

Основной сайт по адресу http://localhost

Админ-панель по адресу http://localhost/admin


### Через docker-compose, локально

1. Создайте файл .env в директории infra и добавьте туда следующие переменные

```
DEBUG=True
SECRET_KEY=...
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.postgresql
DB_NAME=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
DB_HOST=...
DB_PORT=5432
DJANGO_SETTINGS_MODULE=server.settings
```

2. Запустите docker-compose из директории infra
``` bash
docker-compose up --build
```
3. Прогнать postman_collection можно во время запущенных докер-контейнеров, для этого сначала удалите контейнеры и тома, а затем снова запустите приложение командой из предыдущего пункта
``` bash
docker-compose down -v
```
