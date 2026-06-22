#!/bin/bash

echo "🚀 Iniciando Django en Render..."

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Iniciar Gunicorn
gunicorn mysite.wsgi:application