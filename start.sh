#!/bin/bash

echo "🚀 Iniciando Django en Render..."

# Instalar dependencias
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --noinput --clear

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# ✅ INICIALIZAR DATOS DE PRUEBA
python manage.py init_db

# Iniciar Gunicorn
gunicorn mysite.wsgi:application
