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
    python manage.py load_ingredients
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

Основной сайт по адресу http://127.0.0.1:8000

Админ-панель по адресу http://127.0.0.1:8000/admin


### Через docker-compose, локально

1. Создайте файл .env в директории infra и добавьте туда следующие переменные

```
SECRET_KEY=<секретный ключ Django>
ALLOWED_HOSTS=<разрешенные хосты>
DB_ENGINE=<база данных>
DB_NAME=<имя бд>
DB_HOST=<хост в контейнере>
DB_PORT=5432
POSTGRES_USER=<пользователь postgresql>
POSTGRES_PASSWORD=<пароль postgresql>
POSTGRES_DB=<бд в postgresql>
```

2. Запустите docker-compose из директории infra и примените миграции и сборку статики
``` bash
docker-compose up -d
docker-compose exec foodgram-backend python manage.py collectstatic
docker-compose exec foodgram-backend cp -r /app/collected_static/. /static/static/
```

### На удаленном сервере
1. Установите Docker Compose на ваш удаленный сервер

2. Скачайте файл docker-compose.production.yml на сервер

3. Аналогично предыдущему способу создайте файл .env

4. Запустите проект командой
``` bash
docker-compose -f docker-compose.production.yml up -d
```