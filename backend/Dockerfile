FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
     && pip install -r requirements.txt --no-cache-dir --default-timeout=100

COPY . .

CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate \
                   && python manage.py load_ingredients \
                   && gunicorn main.wsgi:application --bind 0.0.0.0:8000"]
