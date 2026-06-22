#!/bin/bash

echo "🚀 Iniciando Django en Render..."

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear || true

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py makemigrations || true
python manage.py migrate || true

# Inicializar datos (si no hay datos)
echo "📊 Inicializando datos..."
python manage.py init_db || true

# Iniciar Gunicorn
echo "🚀 Iniciando servidor..."
gunicorn mysite.wsgi:application
