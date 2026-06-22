#!/bin/bash

echo "🚀 Iniciando Django en Render..."

# Instalar dependencias
pip install -r requirements.txt

# ✅ RECOLECTAR ARCHIVOS ESTÁTICOS
python manage.py collectstatic --noinput

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# Iniciar Gunicorn con Django
gunicorn mysite.wsgi:application
