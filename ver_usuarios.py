from inventario_app.models import Inventario
from django.contrib.auth.models import User

print("="*50)
print("USUARIOS Y SUS INVENTARIOS")
print("="*50)

for user in User.objects.all():
    if user.is_superuser:
        print(f"{user.email} -> Admin")
    else:
        try:
            # Obtener el inventario basado en el nombre de usuario
            nombre_inventario = user.username.split('@')[0]
            inv = Inventario.objects.get(nombre=nombre_inventario)
            productos = inv.producto_set.count()
            print(f"{user.email} -> {inv.nombre}: {productos} productos")
        except Inventario.DoesNotExist:
            print(f"{user.email} -> Sin inventario asignado")
        except Exception as e:
            print(f"{user.email} -> Error: {str(e)}")

print("="*50)
print("TODOS LOS INVENTARIOS")
print("="*50)

for inv in Inventario.objects.all():
    productos = inv.producto_set.count()
    print(f"{inv.nombre}: {productos} productos")