FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=server.settings

RUN chmod +x /app/entrypoint.sh

CMD ["gunicorn", "server.wsgi:application", "--bind", "0.0.0.0:8000"] 