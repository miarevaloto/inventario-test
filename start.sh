#!/bin/bash

echo "🚀 Iniciando Django en Render..."

# Verificar que los archivos estáticos existen
echo "📁 Verificando archivos estáticos..."
ls -la static/

# ✅ RECOLECTAR ARCHIVOS ESTÁTICOS
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Verificar que se recolectaron
echo "📁 Archivos recolectados:"
ls -la staticfiles/

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py makemigrations
python manage.py migrate

# Iniciar Gunicorn
echo "🚀 Iniciando servidor..."
gunicorn mysite.wsgi:application
