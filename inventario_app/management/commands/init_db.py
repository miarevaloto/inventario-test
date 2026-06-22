from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventario_app.models import Inventario, Producto, Venta, UsuarioInventario
import random
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Inicializa la base de datos con 4 tiendas de repuestos'

    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write("🏍️  CREANDO 4 TIENDAS DE REPUESTOS")
        self.stdout.write("="*60)
        
        if Inventario.objects.exists():
            self.stdout.write(self.style.SUCCESS("✅ Base de datos ya inicializada"))
            return
        
        tiendas = [
            {"nombre": "Repmotos", "email": "repmotos@email.com", "password": "123456", 
             "factor_precio": 1.0, "stock_base": 100, "num_productos": 20, "ventas_por_dia": 3, "dias_historial": 45},
            {"nombre": "MotoPartes SAS", "email": "motopartes@email.com", "password": "mp2024", 
             "factor_precio": 0.85, "stock_base": 150, "num_productos": 20, "ventas_por_dia": 5, "dias_historial": 60},
            {"nombre": "Rapimotos", "email": "rapimotos@email.com", "password": "rapi123", 
             "factor_precio": 1.20, "stock_base": 60, "num_productos": 18, "ventas_por_dia": 2, "dias_historial": 30},
            {"nombre": "Motorepuestos Plus", "email": "motoplus@email.com", "password": "plus2024", 
             "factor_precio": 0.90, "stock_base": 200, "num_productos": 25, "ventas_por_dia": 4, "dias_historial": 50}
        ]
        
        productos_base = [
            {"nombre": "Aceite 4T", "categoria": "Lubricantes", "precio_base": 25000},
            {"nombre": "Filtro de aire", "categoria": "Repuestos", "precio_base": 15000},
            {"nombre": "Bujía NGK", "categoria": "Repuestos", "precio_base": 10000},
            {"nombre": "Casco integral", "categoria": "Accesorios", "precio_base": 120000},
            {"nombre": "Guantes moto", "categoria": "Accesorios", "precio_base": 30000},
            {"nombre": "Cadena moto", "categoria": "Transmisión", "precio_base": 80000},
            {"nombre": "Kit arrastre", "categoria": "Transmisión", "precio_base": 150000},
            {"nombre": "Llanta delantera", "categoria": "Llantas", "precio_base": 90000},
            {"nombre": "Llanta trasera", "categoria": "Llantas", "precio_base": 110000},
            {"nombre": "Pastillas de freno", "categoria": "Frenos", "precio_base": 20000},
            {"nombre": "Manillar", "categoria": "Repuestos", "precio_base": 45000},
            {"nombre": "Espejos retrovisores", "categoria": "Accesorios", "precio_base": 12000},
            {"nombre": "Batería moto", "categoria": "Eléctricos", "precio_base": 85000},
            {"nombre": "Luces LED", "categoria": "Accesorios", "precio_base": 25000},
            {"nombre": "Disco de freno", "categoria": "Frenos", "precio_base": 35000},
            {"nombre": "Bomba de freno", "categoria": "Frenos", "precio_base": 55000},
            {"nombre": "Cable de acelerador", "categoria": "Repuestos", "precio_base": 18000},
            {"nombre": "Regulador de voltaje", "categoria": "Eléctricos", "precio_base": 42000},
            {"nombre": "Bobina de encendido", "categoria": "Eléctricos", "precio_base": 38000},
            {"nombre": "Carburador", "categoria": "Motor", "precio_base": 95000},
        ]
        
        # Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@email.com', 'admin123')
            self.stdout.write("   ✅ Admin: admin@email.com / admin123")
        
        inv_principal = Inventario.objects.create(nombre="Principal")
        inv_test = Inventario.objects.create(nombre="Test")
        self.stdout.write("   ✅ Inventario Test creado (vacío)")
        
        # Crear tiendas
        for tienda in tiendas:
            if not User.objects.filter(username=tienda['email']).exists():
                user = User.objects.create_user(
                    username=tienda['email'],
                    email=tienda['email'],
                    password=tienda['password']
                )
                self.stdout.write(f"   👤 {tienda['email']} / {tienda['password']}")
                
                inv = Inventario.objects.create(nombre=tienda['nombre'])
                
                # ✅ CREAR RELACIÓN USUARIO-INVENTARIO
                UsuarioInventario.objects.create(usuario=user, inventario=inv)
                
                # Productos
                for i in range(min(tienda['num_productos'], len(productos_base))):
                    prod_base = productos_base[i]
                    variacion = random.uniform(0.95, 1.05)
                    precio = round(prod_base['precio_base'] * tienda['factor_precio'] * variacion, 2)
                    stock_variacion = random.randint(-30, 30)
                    stock = max(0, tienda['stock_base'] + stock_variacion)
                    
                    Producto.objects.create(
                        nombre=prod_base['nombre'],
                        categoria=prod_base['categoria'],
                        cantidad=stock,
                        precio=precio,
                        inventario=inv
                    )
                
                # Ventas
                ventas_creadas = 0
                for dia in range(tienda['dias_historial']):
                    num_ventas_dia = max(1, int(tienda['ventas_por_dia'] * random.uniform(0.5, 1.5)))
                    for _ in range(num_ventas_dia):
                        productos = Producto.objects.filter(inventario=inv)
                        if productos.exists():
                            producto = random.choice(list(productos[:15]))
                            if producto.precio < 20000:
                                cantidad = random.randint(2, 8)
                            elif producto.precio < 100000:
                                cantidad = random.randint(1, 4)
                            else:
                                cantidad = random.randint(1, 2)
                            
                            descuento = random.uniform(0, 0.15)
                            precio_venta = round(producto.precio * (1 - descuento), 2)
                            fecha = timezone.now() - timedelta(days=dia)
                            
                            Venta.objects.create(
                                producto=producto.nombre,
                                cantidad=cantidad,
                                precio=precio_venta,
                                fecha=fecha,
                                inventario=inv
                            )
                            ventas_creadas += 1
                            producto.cantidad = max(0, producto.cantidad - cantidad)
                            producto.save()
                
                self.stdout.write(f"   ✅ {tienda['nombre']}: {Producto.objects.filter(inventario=inv).count()} productos, {ventas_creadas} ventas")
        
        self.stdout.write(self.style.SUCCESS("✅ Base de datos inicializada con 4 tiendas"))