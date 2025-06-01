#!/bin/bash

set -e

python manage.py makemigrations
python manage.py migrate
python manage.py init_data
python manage.py collectstatic --noinput
python manage.py test --keepdb

flake8 . --extend-ignore=D --exclude=migrations,__pycache__ --max-line-length=119

gunicorn server.wsgi:application --bind 0.0.0.0:8000 