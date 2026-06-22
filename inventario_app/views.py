from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import random
from datetime import timedelta

from .models import Inventario, Producto, Venta, UsuarioInventario
from .utils import generar_reporte_pdf

# ================= LOGIN =================
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Correo y contraseña son requeridos')
            return render(request, 'inventario_app/login.html')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Credenciales incorrectas')
    
    return render(request, 'inventario_app/login.html')

# ================= REGISTER =================
def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Correo y contraseña son requeridos')
            return render(request, 'inventario_app/register.html')
        
        if '@' not in email or '.' not in email:
            messages.error(request, 'Formato de correo inválido')
            return render(request, 'inventario_app/register.html')
        
        if len(password) < 4:
            messages.error(request, 'La contraseña debe tener al menos 4 caracteres')
            return render(request, 'inventario_app/register.html')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Usuario ya existe')
            return render(request, 'inventario_app/register.html')
        
        user = User.objects.create_user(username=email, email=email, password=password)
        inventario = Inventario.objects.create(nombre=f'Inventario de {email}')
        UsuarioInventario.objects.create(usuario=user, inventario=inventario)
        
        messages.success(request, 'Usuario creado correctamente')
        return redirect('login')
    
    return render(request, 'inventario_app/register.html')

# ================= LOGOUT =================
def logout_view(request):
    logout(request)
    return redirect('login')

# ================= INDEX =================
@login_required
def index(request):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    productos = Producto.objects.filter(inventario=inventario)
    categorias = Producto.objects.filter(inventario=inventario).values_list('categoria', flat=True).distinct()
    
    return render(request, 'inventario_app/index.html', {
        'productos': productos,
        'categorias': categorias,
        'nombre': request.user.email
    })

# ================= DASHBOARD =================
@login_required
def dashboard(request):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    total_productos = Producto.objects.filter(inventario=inventario).count()
    stock_total = Producto.objects.filter(inventario=inventario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    ventas_total = Venta.objects.filter(inventario=inventario).aggregate(total=Sum('cantidad') * Sum('precio'))['total'] or 0
    top_productos = Venta.objects.filter(inventario=inventario).values('producto').annotate(vendidos=Sum('cantidad')).order_by('-vendidos')[:5]
    productos_bajo_stock = Producto.objects.filter(inventario=inventario, cantidad__lt=5).order_by('cantidad')
    
    return render(request, 'inventario_app/dashboard.html', {
        'total_productos': total_productos,
        'stock_total': stock_total,
        'ventas_total': ventas_total,
        'top_productos': top_productos,
        'productos_bajo_stock': productos_bajo_stock
    })

# ================= VENTAS =================
@login_required
def ventas(request):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    productos = Producto.objects.filter(inventario=inventario)
    ventas_list = Venta.objects.filter(inventario=inventario).order_by('-id')
    total_ventas = Venta.objects.filter(inventario=inventario).aggregate(total=Sum('cantidad') * Sum('precio'))['total'] or 0
    
    return render(request, 'inventario_app/ventas.html', {
        'productos': productos,
        'ventas': ventas_list,
        'total_ventas': total_ventas
    })

# ================= BUSCAR PRODUCTO =================
@login_required
def buscar_producto(request):
    if request.method == 'POST':
        try:
            producto_id = int(request.POST.get('id'))
            try:
                perfil = UsuarioInventario.objects.get(usuario=request.user)
                inventario = perfil.inventario
            except UsuarioInventario.DoesNotExist:
                inventario = Inventario.objects.first()
            
            producto = get_object_or_404(Producto, id=producto_id, inventario=inventario)
            return JsonResponse({
                'success': True,
                'nombre': producto.nombre,
                'categoria': producto.categoria,
                'cantidad': producto.cantidad,
                'precio': str(producto.precio)
            })
        except:
            return JsonResponse({'success': False, 'error': 'Producto no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# ================= AGREGAR PRODUCTO =================
@login_required
def agregar_producto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio')
        cantidad = request.POST.get('cantidad')
        categoria = request.POST.get('categoria_select', '').strip()
        nueva_categoria = request.POST.get('nueva_categoria', '').strip()
        
        if not nombre or not precio or not cantidad:
            messages.error(request, 'Todos los campos son requeridos')
            return redirect('index')
        
        try:
            precio = float(precio)
            cantidad = int(cantidad)
        except ValueError:
            messages.error(request, 'Precio o cantidad inválidos')
            return redirect('index')
        
        if precio <= 0 or cantidad <= 0:
            messages.error(request, 'Precio y cantidad deben ser mayores a 0')
            return redirect('index')
        
        if categoria == 'nueva' and nueva_categoria:
            categoria = nueva_categoria
        elif categoria == 'nueva':
            messages.error(request, 'Debe ingresar un nombre para la nueva categoría')
            return redirect('index')
        
        try:
            perfil = UsuarioInventario.objects.get(usuario=request.user)
            inventario = perfil.inventario
        except UsuarioInventario.DoesNotExist:
            inventario = Inventario.objects.first()
        
        try:
            Producto.objects.create(
                nombre=nombre,
                categoria=categoria,
                cantidad=cantidad,
                precio=precio,
                inventario=inventario
            )
            messages.success(request, f'✅ Producto "{nombre}" agregado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al agregar producto: {str(e)}')
    
    return redirect('index')

# ================= ELIMINAR PRODUCTO =================
@login_required
def delete_producto(request, id):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    producto = get_object_or_404(Producto, id=id, inventario=inventario)
    producto.delete()
    messages.success(request, '✅ Producto eliminado')
    return redirect('index')

# ================= SUMAR STOCK =================
@login_required
def sumar_stock(request, id):
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad'))
            if cantidad <= 0:
                messages.error(request, 'Cantidad inválida')
                return redirect('index')
            
            try:
                perfil = UsuarioInventario.objects.get(usuario=request.user)
                inventario = perfil.inventario
            except UsuarioInventario.DoesNotExist:
                inventario = Inventario.objects.first()
            
            producto = get_object_or_404(Producto, id=id, inventario=inventario)
            producto.cantidad += cantidad
            producto.save()
            messages.success(request, f'✅ Se agregaron {cantidad} unidades al stock')
        except:
            messages.error(request, '❌ Error al actualizar stock')
    
    return redirect('index')

# ================= VENDER DESDE INDEX =================
@login_required
def vender_producto(request, id):
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad'))
            if cantidad <= 0:
                messages.error(request, 'Cantidad inválida')
                return redirect('index')
            
            try:
                perfil = UsuarioInventario.objects.get(usuario=request.user)
                inventario = perfil.inventario
            except UsuarioInventario.DoesNotExist:
                inventario = Inventario.objects.first()
            
            producto = get_object_or_404(Producto, id=id, inventario=inventario)
            
            if cantidad > producto.cantidad:
                messages.error(request, '❌ Stock insuficiente')
                return redirect('index')
            
            producto.cantidad -= cantidad
            producto.save()
            
            Venta.objects.create(
                producto=producto.nombre,
                cantidad=cantidad,
                precio=producto.precio,
                inventario=inventario
            )
            
            messages.success(request, f'✅ Venta realizada: {cantidad} x {producto.nombre}')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('index')

# ================= REGISTRAR VENTA DESDE VENTAS =================
@login_required
def registrar_venta(request):
    if request.method == 'POST':
        try:
            producto_id = int(request.POST.get('producto_id'))
            cantidad = int(request.POST.get('cantidad'))
            
            if cantidad <= 0:
                messages.error(request, 'Cantidad inválida')
                return redirect('ventas')
            
            try:
                perfil = UsuarioInventario.objects.get(usuario=request.user)
                inventario = perfil.inventario
            except UsuarioInventario.DoesNotExist:
                inventario = Inventario.objects.first()
            
            producto = get_object_or_404(Producto, id=producto_id, inventario=inventario)
            
            if cantidad > producto.cantidad:
                messages.error(request, '❌ Stock insuficiente')
                return redirect('ventas')
            
            producto.cantidad -= cantidad
            producto.save()
            
            Venta.objects.create(
                producto=producto.nombre,
                cantidad=cantidad,
                precio=producto.precio,
                inventario=inventario
            )
            
            messages.success(request, f'✅ Venta registrada: {cantidad} x {producto.nombre}')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('ventas')

# ================= REPORTE PDF =================
@login_required
def reporte_pdf(request):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    productos = Producto.objects.filter(inventario=inventario).order_by('categoria', 'nombre')
    return generar_reporte_pdf(request.user.email, productos)

# ================= ADMIN PANEL =================
@login_required
def admin_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos de administrador')
        return redirect('index')
    
    usuarios = User.objects.all()
    inventarios = Inventario.objects.all()
    
    return render(request, 'inventario_app/admin.html', {
        'usuarios': usuarios,
        'inventarios': inventarios
    })

# ================= CREAR USUARIO ADMIN =================

def crear_admin_sin_login(request):
    """Crea admin y test sin necesidad de login (solo para primera configuración en Render)"""
    try:
        resultado = []
        
        # Crear admin
        if not User.objects.filter(username='admin@email.com').exists():
            User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
            resultado.append("✅ Admin creado: admin@email.com / admin123")
        else:
            resultado.append("✅ Admin ya existe")
        
        # Crear test
        if not User.objects.filter(username='test@email.com').exists():
            User.objects.create_user('test@email.com', 'test@email.com', '1234')
            resultado.append("✅ Test creado: test@email.com / 1234")
        else:
            resultado.append("✅ Test ya existe")
        
        # Verificar inventario Test
        try:
            inv_test = Inventario.objects.get(nombre='Test')
            resultado.append("✅ Inventario Test encontrado")
        except Inventario.DoesNotExist:
            inv_test = Inventario.objects.create(nombre='Test')
            resultado.append("✅ Inventario Test creado")
        
        # Verificar relación test-inventario
        user = User.objects.get(username='test@email.com')
        if not UsuarioInventario.objects.filter(usuario=user).exists():
            UsuarioInventario.objects.create(usuario=user, inventario=inv_test)
            resultado.append("✅ Relación test-inventario creada")
        
        # Mostrar todos los usuarios
        resultado.append("")
        resultado.append("📋 USUARIOS EN LA BASE DE DATOS:")
        for u in User.objects.all():
            es_admin = "👑 Admin" if u.is_superuser else "👤 Usuario"
            resultado.append(f"   {u.email} - {es_admin}")
        
        html = "<h1>🚀 Usuarios creados exitosamente</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al Login</a>"
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}<br><br><a href='/login'>Volver</a>")
# ================= ELIMINAR USUARIO =================
@login_required
def eliminar_usuario(request, id):
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos de administrador')
        return redirect('index')
    
    if id == request.user.id:
        messages.error(request, 'No puedes eliminarte a ti mismo')
        return redirect('admin_panel')
    
    try:
        user = User.objects.get(id=id)
        
        try:
            perfil = UsuarioInventario.objects.get(usuario=user)
            inventario = perfil.inventario
            perfil.delete()
            
            if not UsuarioInventario.objects.filter(inventario=inventario).exists():
                Producto.objects.filter(inventario=inventario).delete()
                Venta.objects.filter(inventario=inventario).delete()
                inventario.delete()
        except UsuarioInventario.DoesNotExist:
            pass
        
        user.delete()
        messages.success(request, '✅ Usuario eliminado')
    except Exception as e:
        messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('admin_panel')

def crear_admin_y_test(request):
    """Crea admin y test sin necesidad de login (solo para primera configuración)"""
    try:
        resultado = []
        
        # Crear admin
        if not User.objects.filter(username='admin@email.com').exists():
            User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
            resultado.append("✅ Admin creado: admin@email.com / admin123")
        else:
            resultado.append("✅ Admin ya existe")
        
        # Crear test
        if not User.objects.filter(username='test@email.com').exists():
            User.objects.create_user('test@email.com', 'test@email.com', '1234')
            resultado.append("✅ Test creado: test@email.com / 1234")
        else:
            resultado.append("✅ Test ya existe")
        
        # Verificar inventario Test
        try:
            inv_test = Inventario.objects.get(nombre='Test')
            resultado.append("✅ Inventario Test encontrado")
        except Inventario.DoesNotExist:
            inv_test = Inventario.objects.create(nombre='Test')
            resultado.append("✅ Inventario Test creado")
        
        # Verificar relación test-inventario
        user = User.objects.get(username='test@email.com')
        if not UsuarioInventario.objects.filter(usuario=user).exists():
            UsuarioInventario.objects.create(usuario=user, inventario=inv_test)
            resultado.append("✅ Relación test-inventario creada")
        
        html = "<h1>🚀 Usuarios creados</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al Login</a>"
        
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}<br><br><a href='/login'>Volver</a>")

# ================= CREAR INVENTARIO =================
@login_required
def crear_inventario(request):
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos de administrador')
        return redirect('index')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if nombre:
            Inventario.objects.create(nombre=nombre)
            messages.success(request, f'✅ Inventario "{nombre}" creado exitosamente')
        else:
            messages.error(request, '❌ Nombre inválido')
    
    return redirect('admin_panel')

# ================= INICIALIZAR BASE DE DATOS =================
def inicializar_bd(request):
    """Endpoint para inicializar la base de datos desde el navegador"""
    
    # Verificar si el usuario es admin
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponse("❌ Debes iniciar sesión como administrador para ejecutar esto.")
    
    try:
        # Verificar si ya hay datos
        if Inventario.objects.exists():
            return HttpResponse("✅ La base de datos ya está inicializada.")
        
        resultado = []
        
        # DEFINIR LAS 4 TIENDAS
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
        
        # CATÁLOGO DE PRODUCTOS
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
        
        # CREAR ADMIN
        if not User.objects.filter(username='admin@email.com').exists():
            User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
            resultado.append("✅ Admin: admin@email.com / admin123")
        else:
            resultado.append("✅ Admin ya existe")
        
        # CREAR INVENTARIOS
        inv_principal = Inventario.objects.create(nombre="Principal")
        inv_test = Inventario.objects.create(nombre="Test")
        resultado.append("✅ Inventario Principal y Test creados")
        
        # CREAR TIENDAS
        for tienda in tiendas:
            if not User.objects.filter(username=tienda['email']).exists():
                user = User.objects.create_user(
                    username=tienda['email'],
                    email=tienda['email'],
                    password=tienda['password']
                )
                resultado.append(f"👤 {tienda['email']} / {tienda['password']}")
            else:
                user = User.objects.get(username=tienda['email'])
                resultado.append(f"👤 {tienda['email']} (ya existe)")
            
            inv = Inventario.objects.create(nombre=tienda['nombre'])
            UsuarioInventario.objects.create(usuario=user, inventario=inv)
            
            # PRODUCTOS
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
            
            # VENTAS ALEATORIAS
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
            
            resultado.append(f"✅ {tienda['nombre']}: {Producto.objects.filter(inventario=inv).count()} productos, {ventas_creadas} ventas")
        
        # CREAR USUARIO TEST
        if not User.objects.filter(username='test@email.com').exists():
            user = User.objects.create_user('test@email.com', 'test@email.com', '1234')
            resultado.append("✅ Test: test@email.com / 1234")
        else:
            user = User.objects.get(username='test@email.com')
            resultado.append("✅ Test ya existe")
        
        if not UsuarioInventario.objects.filter(usuario=user).exists():
            UsuarioInventario.objects.create(usuario=user, inventario=inv_test)
            resultado.append("✅ Relación test-inventario creada")
        
        resultado.append("✅ Base de datos inicializada exitosamente!")
        
        html = "<h1>🚀 Base de datos inicializada</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al Login</a>"
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}<br><br><a href='/'>Volver</a>")
