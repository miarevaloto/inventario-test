#!/bin/bash

echo "🚀 Iniciando Django en Render..."

# Instalar dependencias
pip install -r requirements.txt

# ✅ RECOLECTAR ARCHIVOS ESTÁTICOS
python manage.py collectstatic --noinput --clear

# ✅ EJECUTAR MIGRACIONES
python manage.py makemigrations
python manage.py migrate

# ✅ INICIALIZAR DATOS (CREAR TODOS LOS USUARIOS Y TIENDAS)
python manage.py init_db

# ✅ CREAR USUARIO TEST SI NO EXISTE
python manage.py shell << EOF
from django.contrib.auth.models import User
from inventario_app.models import Inventario, UsuarioInventario

# Crear test si no existe
if not User.objects.filter(username='test@email.com').exists():
    user = User.objects.create_user('test@email.com', 'test@email.com', '1234')
    print("✅ Test creado")
else:
    user = User.objects.get(username='test@email.com')
    print("✅ Test ya existe")

# Asegurar inventario Test
try:
    inv_test = Inventario.objects.get(nombre='Test')
except Inventario.DoesNotExist:
    inv_test = Inventario.objects.create(nombre='Test')
    print("✅ Inventario Test creado")

# Asegurar relación
if not UsuarioInventario.objects.filter(usuario=user).exists():
    UsuarioInventario.objects.create(usuario=user, inventario=inv_test)
    print("✅ Relación test creada")

print("✅ Todos los usuarios listos!")
EOF

# Iniciar Gunicorn
gunicorn mysite.wsgi:application
