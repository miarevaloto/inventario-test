from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse
import random
from datetime import timedelta

from .models import Inventario, Producto, Venta, UsuarioInventario
from .utils import generar_reporte_pdf

# ================= INICIALIZACIÓN =================
def init_db():
    """Crea datos de prueba si la base está vacía"""
    if Inventario.objects.exists():
        print("✅ Base de datos ya inicializada")
        return
    
    print("="*60)
    print("🏍️  CREANDO 4 TIENDAS DE REPUESTOS DE MOTOS")
    print("="*60)
    
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
        print("   ✅ Admin: admin@email.com / admin123")
    
    inv_principal = Inventario.objects.create(nombre="Principal")
    inv_test = Inventario.objects.create(nombre="Test")
    print("   ✅ Inventario Test creado (vacío)")
    
    # Crear tiendas
    for tienda in tiendas:
        if not User.objects.filter(username=tienda['email']).exists():
            user = User.objects.create_user(
                username=tienda['email'],
                email=tienda['email'],
                password=tienda['password']
            )
            print(f"   👤 {tienda['email']} / {tienda['password']}")
            
            inv = Inventario.objects.create(nombre=tienda['nombre'])
            
            # ✅ CREAR LA RELACIÓN USUARIO-INVENTARIO
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
            
            # Stock crítico
            for nombre_critico in ["Pastillas de freno", "Bujía NGK", "Aceite 4T"][:3]:
                producto = Producto.objects.filter(nombre=nombre_critico, inventario=inv).first()
                if producto:
                    producto.cantidad = random.randint(0, 3)
                    producto.save()
            
            print(f"   ✅ {tienda['nombre']}: {Producto.objects.filter(inventario=inv).count()} productos, {ventas_creadas} ventas")
    
    print("✅ Base de datos inicializada con 4 tiendas")

# ================= VISTAS =================
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

def register_view(request):
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
        
        # Crear usuario
        user = User.objects.create_user(username=email, email=email, password=password)
        
        # Crear inventario para el usuario
        inventario = Inventario.objects.create(nombre=f'Inventario de {email}')
        
        # ✅ CREAR LA RELACIÓN USUARIO-INVENTARIO
        UsuarioInventario.objects.create(usuario=user, inventario=inventario)
        
        messages.success(request, 'Usuario creado correctamente')
        return redirect('login')
    
    return render(request, 'inventario_app/register.html')

@login_required
def index(request):
    try:
        # ✅ Obtener el inventario del usuario desde la relación
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        # Si no tiene perfil, crear uno con el primer inventario disponible
        inventario = Inventario.objects.first()
        if inventario:
            UsuarioInventario.objects.create(usuario=request.user, inventario=inventario)
        else:
            inventario = Inventario.objects.create(nombre="Principal")
    
    productos = Producto.objects.filter(inventario=inventario)
    categorias = Producto.objects.filter(inventario=inventario).values_list('categoria', flat=True).distinct()
    
    return render(request, 'inventario_app/index.html', {
        'productos': productos,
        'categorias': categorias,
        'nombre': request.user.email
    })

@login_required
def dashboard(request):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    total_productos = Producto.objects.filter(inventario=inventario).count()
    stock_total = Producto.objects.filter(inventario=inventario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    
    ventas_total = Venta.objects.filter(inventario=inventario).aggregate(
        total=Sum('cantidad') * Sum('precio')
    )['total'] or 0
    
    top_productos = Venta.objects.filter(inventario=inventario).values('producto').annotate(
        vendidos=Sum('cantidad')
    ).order_by('-vendidos')[:5]
    
    productos_bajo_stock = Producto.objects.filter(
        inventario=inventario,
        cantidad__lt=5
    ).order_by('cantidad')
    
    return render(request, 'inventario_app/dashboard.html', {
        'total_productos': total_productos,
        'stock_total': stock_total,
        'ventas_total': ventas_total,
        'top_productos': top_productos,
        'productos_bajo_stock': productos_bajo_stock
    })

@login_required
def ventas(request):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    # ✅ OBTENER PRODUCTOS DEL INVENTARIO
    productos = Producto.objects.filter(inventario=inventario)
    
    # ✅ OBTENER VENTAS
    ventas_list = Venta.objects.filter(inventario=inventario).order_by('-id')
    
    # ✅ CALCULAR TOTAL
    total_ventas = Venta.objects.filter(inventario=inventario).aggregate(
        total=Sum('cantidad') * Sum('precio')
    )['total'] or 0
    
    return render(request, 'inventario_app/ventas.html', {
        'productos': productos,      # ✅ ESTO ES OBLIGATORIO
        'ventas': ventas_list,
        'total_ventas': total_ventas
    })

@login_required
def reporte_pdf(request):
    try:
        perfil = UsuarioInventario.objects.get(usuario=request.user)
        inventario = perfil.inventario
    except UsuarioInventario.DoesNotExist:
        inventario = Inventario.objects.first()
    
    productos = Producto.objects.filter(inventario=inventario).order_by('categoria', 'nombre')
    return generar_reporte_pdf(request.user.email, productos)

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
            
            # Actualizar stock
            producto.cantidad -= cantidad
            producto.save()
            
            # Registrar venta
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

@login_required
def registrar_venta(request):
    if request.method == 'POST':
        try:
            producto_id = int(request.POST.get('producto_id'))
            cantidad = int(request.POST.get('cantidad'))
            
            if cantidad <= 0:
                messages.error(request, '❌ Cantidad inválida')
                return redirect('ventas')
            
            # Obtener inventario del usuario
            try:
                perfil = UsuarioInventario.objects.get(usuario=request.user)
                inventario = perfil.inventario
            except UsuarioInventario.DoesNotExist:
                inventario = Inventario.objects.first()
            
            # Obtener producto
            producto = get_object_or_404(Producto, id=producto_id, inventario=inventario)
            
            # Verificar stock
            if cantidad > producto.cantidad:
                messages.error(request, f'❌ Stock insuficiente. Solo hay {producto.cantidad} unidades')
                return redirect('ventas')
            
            # Actualizar stock
            producto.cantidad -= cantidad
            producto.save()
            
            # Registrar venta
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

@login_required
def crear_usuario_admin(request):
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos de administrador')
        return redirect('index')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol', 'usuario')
        inventario_id = request.POST.get('inventario_id')
        nuevo_inventario = request.POST.get('nuevo_inventario', '').strip()
        
        if not email or not password:
            messages.error(request, 'Todos los campos son requeridos')
            return redirect('admin_panel')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'El correo ya está registrado')
            return redirect('admin_panel')
        
        try:
            # Crear usuario
            user = User.objects.create_user(username=email, email=email, password=password)
            
            if rol == 'admin':
                user.is_superuser = True
                user.is_staff = True
                user.save()
            
            # Asignar inventario
            if inventario_id and inventario_id != 'nuevo':
                inventario = Inventario.objects.get(id=inventario_id)
            elif nuevo_inventario:
                inventario = Inventario.objects.create(nombre=nuevo_inventario)
            else:
                inventario = Inventario.objects.create(nombre=f'Inventario de {email}')
            
            # ✅ CREAR LA RELACIÓN USUARIO-INVENTARIO
            UsuarioInventario.objects.create(usuario=user, inventario=inventario)
            
            messages.success(request, f'✅ Usuario {email} creado exitosamente')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('admin_panel')

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
        
        # Eliminar relación usuario-inventario
        try:
            perfil = UsuarioInventario.objects.get(usuario=user)
            inventario = perfil.inventario
            perfil.delete()
            
            # Verificar si el inventario está siendo usado por otro usuario
            if not UsuarioInventario.objects.filter(inventario=inventario).exists():
                # Eliminar productos y ventas del inventario
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

def logout_view(request):
    logout(request)
    return redirect('login')

# ================= VISTAS PARA ADMINISTRACIÓN DE INVENTARIOS =================
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