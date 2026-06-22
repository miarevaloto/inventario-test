#!/bin/bash

echo "🚀 Iniciando Django en Render..."

# Instalar dependencias
pip install -r requirements.txt

# ✅ RECOLECTAR ARCHIVOS ESTÁTICOS
python manage.py collectstatic --noinput --clear

# Ejecutar migraciones
python manage.py makemigrations || true
python manage.py migrate || true

# Inicializar datos
python manage.py init_db || true

# Iniciar servidor
gunicorn mysite.wsgi:application
