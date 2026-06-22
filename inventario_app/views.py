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

# ================= LOGOUT =================
def logout_view(request):
    logout(request)
    return redirect('login')

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
            user = User.objects.create_user(username=email, email=email, password=password)
            
            if rol == 'admin':
                user.is_superuser = True
                user.is_staff = True
                user.save()
            
            if inventario_id and inventario_id != 'nuevo':
                inventario = Inventario.objects.get(id=inventario_id)
            elif nuevo_inventario:
                inventario = Inventario.objects.create(nombre=nuevo_inventario)
            else:
                inventario = Inventario.objects.create(nombre=f'Inventario de {email}')
            
            UsuarioInventario.objects.create(usuario=user, inventario=inventario)
            
            messages.success(request, f'✅ Usuario {email} creado exitosamente')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('admin_panel')

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
