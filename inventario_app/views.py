from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import random
import traceback
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
        inventario = Inventario.objects.create(nombre=f"Inventario de {request.user.email}")
        UsuarioInventario.objects.create(usuario=request.user, inventario=inventario)
    
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
        inventario = Inventario.objects.create(nombre=f"Inventario de {request.user.email}")
        UsuarioInventario.objects.create(usuario=request.user, inventario=inventario)
    
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
        inventario = Inventario.objects.create(nombre=f"Inventario de {request.user.email}")
        UsuarioInventario.objects.create(usuario=request.user, inventario=inventario)
    
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
    if "user_id" not in session:
        return redirect("/login")

    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.utils import ImageReader
        from datetime import datetime
        from django.db.models import Sum, Count
        import os
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), 
                                leftMargin=0.5*inch, rightMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = getSampleStyleSheet()
        
        # ============================================================
        # 1. ESTILOS
        # ============================================================
        titulo_style = ParagraphStyle(
            'TituloStyle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#1a4d8c'),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        subtitulo_style = ParagraphStyle(
            'SubtituloStyle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            spaceAfter=15
        )
        
        seccion_style = ParagraphStyle(
            'SeccionStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a4d8c'),
            spaceAfter=10,
            spaceBefore=15
        )
        
        story = []
        
        # ============================================================
        # 2. CABECERA CON LOGO
        # ============================================================
        try:
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=1.5*inch, height=0.8*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 5))
        except:
            pass
        
        story.append(Paragraph("MOTOSTOCK PRO", titulo_style))
        story.append(Paragraph("Sistema de Gestión de Inventarios", subtitulo_style))
        story.append(Paragraph("📦 REPORTE DE INVENTARIO", titulo_style))
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nombre_usuario = session.get('nombre', session.get('email', 'Usuario'))
        story.append(Paragraph(f"Generado por: {nombre_usuario}", styles['Normal']))
        story.append(Paragraph(f"Fecha: {fecha_actual}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # ============================================================
        # 3. DATOS DEL INVENTARIO
        # ============================================================
        try:
            perfil = UsuarioInventario.objects.get(usuario=request.user)
            inventario = perfil.inventario
        except UsuarioInventario.DoesNotExist:
            inventario = Inventario.objects.first()
        
        # ============================================================
        # 4. RESUMEN EJECUTIVO
        # ============================================================
        story.append(Paragraph("RESUMEN EJECUTIVO", seccion_style))
        
        total_productos = Producto.objects.filter(inventario=inventario).count()
        stock_total = Producto.objects.filter(inventario=inventario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        categorias_count = Producto.objects.filter(inventario=inventario).values('categoria').distinct().count()
        ventas_count = Venta.objects.filter(inventario=inventario).count()
        ventas_total = Venta.objects.filter(inventario=inventario).aggregate(total=Sum('cantidad') * Sum('precio'))['total'] or 0
        
        data_resumen = [
            ["Total Productos", "Stock Total", "Categorías", "Total Ventas", "Monto Ventas"],
            [str(total_productos), f"{stock_total:,}", str(categorias_count), str(ventas_count), f"${ventas_total:,.2f}"]
        ]
        
        tabla_resumen = Table(data_resumen, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d8c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e8f0fe')),
        ]))
        story.append(tabla_resumen)
        story.append(Spacer(1, 20))
        
        # ============================================================
        # 5. PRODUCTOS CON STOCK BAJO
        # ============================================================
        productos_bajo_stock = Producto.objects.filter(
            inventario=inventario,
            cantidad__lt=5
        ).order_by('cantidad')
        
        if productos_bajo_stock:
            story.append(Paragraph("⚠️ PRODUCTOS CON STOCK BAJO", seccion_style))
            
            data_bajo = [["Producto", "Stock", "Stock Mínimo", "Estado"]]
            for p in productos_bajo_stock:
                estado = "CRÍTICO" if p.cantidad == 0 else "BAJO"
                data_bajo.append([p.nombre, str(p.cantidad), "5", estado])
            
            tabla_bajo = Table(data_bajo, colWidths=[2.2*inch, 1*inch, 1.2*inch, 1.2*inch])
            tabla_bajo.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff3cd')),
            ]))
            story.append(tabla_bajo)
            story.append(Spacer(1, 20))
        
        # ============================================================
        # 6. TOP 5 PRODUCTOS MÁS VENDIDOS
        # ============================================================
        top_productos = Venta.objects.filter(
            inventario=inventario
        ).values('producto').annotate(
            vendidos=Sum('cantidad')
        ).order_by('-vendidos')[:5]
        
        if top_productos:
            story.append(Paragraph("🏆 TOP 5 PRODUCTOS MÁS VENDIDOS", seccion_style))
            
            data_top = [["Posición", "Producto", "Unidades Vendidas"]]
            for i, p in enumerate(top_productos, 1):
                data_top.append([str(i), p['producto'], str(p['vendidos'])])
            
            tabla_top = Table(data_top, colWidths=[0.8*inch, 2.5*inch, 1.5*inch])
            tabla_top.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(tabla_top)
            story.append(Spacer(1, 20))
        
        # ============================================================
        # 7. LISTA DE PRODUCTOS
        # ============================================================
        story.append(Paragraph("📋 LISTADO DE PRODUCTOS", seccion_style))
        
        productos = Producto.objects.filter(inventario=inventario).order_by('categoria', 'nombre')
        
        if productos:
            data = [["ID", "Producto", "Categoría", "Cantidad", "Precio Unit.", "Valor Total"]]
            total_general = 0
            for p in productos:
                valor = p.cantidad * p.precio
                total_general += valor
                data.append([
                    str(p.id),
                    p.nombre,
                    p.categoria,
                    str(p.cantidad),
                    f"${p.precio:,.2f}",
                    f"${valor:,.2f}"
                ])
            data.append(["", "", "", "", "TOTAL GENERAL:", f"${total_general:,.2f}"])
            
            table = Table(data, colWidths=[0.6*inch, 1.8*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d8c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (1, 1), (-1, -2), 8),
                ('ALIGN', (0, 1), (0, -2), 'CENTER'),
                ('ALIGN', (3, 1), (3, -2), 'CENTER'),
                ('ALIGN', (4, 1), (-1, -2), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0fe')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (4, -1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#cccccc')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a4d8c')),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No hay productos en este inventario", styles['Normal']))
        
        # ============================================================
        # 8. PIE DE PÁGINA
        # ============================================================
        story.append(Spacer(1, 30))
        story.append(Paragraph("-" * 80, styles['Normal']))
        story.append(Paragraph(
            f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}",
            styles['Normal']
        ))
        story.append(Paragraph(
            "Este documento es confidencial y de uso exclusivo de la empresa.",
            styles['Normal']
        ))
        story.append(Paragraph(
            "MotoStock PRO - Sistema de Gestión de Inventarios v1.0",
            styles['Normal']
        ))
        
        doc.build(story)
        buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_inventario_{timestamp}.pdf"
        
        return send_file(buffer, as_attachment=True, 
                        download_name=filename, 
                        mimetype='application/pdf')
    
    except Exception as e:
        print(f"❌ Error al generar PDF: {str(e)}", file=sys.stderr)
        flash(f"❌ Error al generar el reporte: {str(e)}")
        return redirect("/index")
        
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

# ================= CREAR ADMIN Y TEST =================
def crear_admin_sin_login(request):
    """Crea admin y test sin necesidad de login"""
    try:
        resultado = []
        
        # Eliminar admin y test existentes
        User.objects.filter(username='admin@email.com').delete()
        User.objects.filter(username='test@email.com').delete()
        
        # Crear admin
        User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
        resultado.append("✅ Admin creado: admin@email.com / admin123")
        
        # Crear test
        User.objects.create_user('test@email.com', 'test@email.com', '1234')
        resultado.append("✅ Test creado: test@email.com / 1234")
        
        # Crear inventario Test
        inv_test, _ = Inventario.objects.get_or_create(nombre='Test')
        resultado.append("✅ Inventario Test creado")
        
        # Asignar test a su inventario
        user_test = User.objects.get(username='test@email.com')
        if not UsuarioInventario.objects.filter(usuario=user_test).exists():
            UsuarioInventario.objects.create(usuario=user_test, inventario=inv_test)
            resultado.append("✅ Relación test-inventario creada")
        
        html = "<h1>🚀 Admin y test creados</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al login</a>"
        
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")

# ================= CREAR TODAS LAS TIENDAS =================
def crear_todo(request):
    """Crea TODAS las tiendas con productos y ventas aleatorias (sin duplicados)"""
    try:
        from django.contrib.auth.models import User
        from .models import Inventario, Producto, Venta, UsuarioInventario
        import random
        from datetime import timedelta
        from django.utils import timezone
        
        resultado = []
        resultado.append("🚀 CREANDO TODAS LAS TIENDAS")
        resultado.append("="*60)
        
        # ========== DEFINIR LAS 4 TIENDAS ==========
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
        
        # ========== CATÁLOGO DE PRODUCTOS ==========
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
        ]
        
        # ========== CREAR CADA TIENDA ==========
        for tienda in tiendas:
            resultado.append(f"\n🏪 {tienda['nombre']}")
            
            # Verificar si el usuario ya existe
            user = User.objects.filter(username=tienda['email']).first()
            if not user:
                user = User.objects.create_user(
                    username=tienda['email'],
                    email=tienda['email'],
                    password=tienda['password']
                )
                resultado.append(f"   👤 {tienda['email']} / {tienda['password']}")
            else:
                resultado.append(f"   👤 {tienda['email']} (ya existe)")
            
            # Verificar si el inventario ya existe
            inv = Inventario.objects.filter(nombre=tienda['nombre']).first()
            if not inv:
                inv = Inventario.objects.create(nombre=tienda['nombre'])
                resultado.append(f"   📦 Inventario {tienda['nombre']} creado")
            else:
                resultado.append(f"   📦 Inventario {tienda['nombre']} ya existe")
            
            # Verificar relación usuario-inventario (evitar duplicados)
            if not UsuarioInventario.objects.filter(usuario=user).exists():
                UsuarioInventario.objects.create(usuario=user, inventario=inv)
                resultado.append(f"   🔗 Relación usuario-inventario creada")
            else:
                resultado.append(f"   🔗 Relación usuario-inventario ya existe")
            
            # ========== CREAR PRODUCTOS (solo si no existen) ==========
            productos_tienda = []
            productos_existentes = Producto.objects.filter(inventario=inv).count()
            
            if productos_existentes == 0:
                for i in range(min(tienda['num_productos'], len(productos_base))):
                    prod_base = productos_base[i]
                    variacion = random.uniform(0.95, 1.05)
                    precio = round(prod_base['precio_base'] * tienda['factor_precio'] * variacion, 2)
                    stock_variacion = random.randint(-30, 30)
                    stock = max(0, tienda['stock_base'] + stock_variacion)
                    
                    producto = Producto.objects.create(
                        nombre=prod_base['nombre'],
                        categoria=prod_base['categoria'],
                        cantidad=stock,
                        precio=precio,
                        inventario=inv
                    )
                    productos_tienda.append({
                        "id": producto.id,
                        "nombre": prod_base['nombre'],
                        "precio": precio,
                        "stock_inicial": stock
                    })
                
                resultado.append(f"   📦 {len(productos_tienda)} productos creados")
            else:
                # Si ya hay productos, solo listarlos
                for p in Producto.objects.filter(inventario=inv):
                    productos_tienda.append({
                        "id": p.id,
                        "nombre": p.nombre,
                        "precio": p.precio,
                        "stock_inicial": p.cantidad
                    })
                resultado.append(f"   📦 {productos_existentes} productos ya existentes")
            
            # ========== GENERAR VENTAS (solo si no hay) ==========
            ventas_existentes = Venta.objects.filter(inventario=inv).count()
            
            if ventas_existentes == 0 and productos_tienda:
                fechas = []
                for i in range(tienda['dias_historial']):
                    fecha = timezone.now() - timedelta(days=i)
                    fechas.append(fecha.strftime("%Y-%m-%d %H:%M:%S"))
                
                ventas_creadas = 0
                for dia in range(tienda['dias_historial']):
                    num_ventas_dia = max(1, int(tienda['ventas_por_dia'] * random.uniform(0.5, 1.5)))
                    for _ in range(num_ventas_dia):
                        if productos_tienda:
                            producto = random.choice(productos_tienda[:15])
                            if producto['precio'] < 20000:
                                cantidad = random.randint(2, 8)
                            elif producto['precio'] < 100000:
                                cantidad = random.randint(1, 4)
                            else:
                                cantidad = random.randint(1, 2)
                            
                            descuento = random.uniform(0, 0.15)
                            precio_venta = round(producto['precio'] * (1 - descuento), 2)
                            fecha_venta = fechas[dia]
                            
                            Venta.objects.create(
                                producto=producto['nombre'],
                                cantidad=cantidad,
                                precio=precio_venta,
                                inventario=inv,
                                fecha=fecha_venta
                            )
                            ventas_creadas += 1
                            
                            # Actualizar stock
                            prod = Producto.objects.get(id=producto['id'])
                            prod.cantidad = max(0, prod.cantidad - cantidad)
                            prod.save()
                
                resultado.append(f"   💰 {ventas_creadas} ventas generadas")
            else:
                resultado.append(f"   💰 {ventas_existentes} ventas ya existentes")
        
        # ========== RESUMEN FINAL ==========
        resultado.append("\n" + "="*60)
        resultado.append("✅ BASE DE DATOS COMPLETA!")
        resultado.append("="*60)
        resultado.append("\n🔐 CREDENCIALES DE ACCESO:")
        resultado.append("   admin@email.com / admin123 (Administrador)")
        for tienda in tiendas:
            resultado.append(f"   {tienda['email']} / {tienda['password']} → {tienda['nombre']}")
        resultado.append("   test@email.com / 1234 (Inventario vacío)")
        
        html = "<h1>🚀 Base de datos creada exitosamente!</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al login</a>"
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}<br><br><a href='/login/'>Volver</a>")
# ================= LIMPIAR BASE DE DATOS =================
def limpiar_todo(request):
    """Limpia toda la base de datos"""
    try:
        resultado = []
        resultado.append("🧹 LIMPIANDO BASE DE DATOS")
        resultado.append("="*50)
        
        # 1. Eliminar ventas
        ventas_count = Venta.objects.count()
        Venta.objects.all().delete()
        resultado.append(f"✅ Ventas eliminadas: {ventas_count}")
        
        # 2. Eliminar productos
        productos_count = Producto.objects.count()
        Producto.objects.all().delete()
        resultado.append(f"✅ Productos eliminados: {productos_count}")
        
        # 3. Eliminar relaciones usuario-inventario
        relaciones_count = UsuarioInventario.objects.count()
        UsuarioInventario.objects.all().delete()
        resultado.append(f"✅ Relaciones eliminadas: {relaciones_count}")
        
        # 4. Eliminar inventarios
        inventarios_count = Inventario.objects.count()
        Inventario.objects.all().delete()
        resultado.append(f"✅ Inventarios eliminados: {inventarios_count}")
        
        # 5. Eliminar usuarios (excepto admin)
        User.objects.exclude(username='admin@email.com').delete()
        resultado.append("✅ Usuarios eliminados (excepto admin)")
        
        # 6. Asegurar que admin existe
        if not User.objects.filter(username='admin@email.com').exists():
            User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
            resultado.append("✅ Admin creado: admin@email.com / admin123")
        
        resultado.append("="*50)
        resultado.append("✅ BASE DE DATOS LIMPIADA!")
        
        html = "<h1>🧹 Base de datos limpiada exitosamente</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/crear_admin/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>1. Crear admin y test</a>"
        html += "<br><br><a href='/crear_todo/' style='padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;'>2. Crear todas las tiendas</a>"
        html += "<br><br><a href='/login/' style='padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 5px;'>3. Ir al login</a>"
        
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")

# ================= REPARAR USUARIOS =================
def reparar_usuarios(request):
    """Repara usuarios sin inventario"""
    try:
        resultado = []
        resultado.append("🔧 REPARANDO USUARIOS")
        resultado.append("="*50)
        
        for user in User.objects.all():
            try:
                perfil = UsuarioInventario.objects.get(usuario=user)
                resultado.append(f"✅ {user.email} -> {perfil.inventario.nombre}")
            except UsuarioInventario.DoesNotExist:
                resultado.append(f"⚠️ {user.email} -> Creando inventario...")
                inventario = Inventario.objects.create(nombre=f"Inventario de {user.email}")
                UsuarioInventario.objects.create(usuario=user, inventario=inventario)
                resultado.append(f"✅ {user.email} -> {inventario.nombre} creado")
        
        resultado.append("="*50)
        resultado.append("✅ REPARACIÓN COMPLETADA")
        
        html = "<h1>🔧 Reparación completada</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al login</a>"
        
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")

def crear_admin_rapido(request):
    """Crea admin y test sin necesidad de login"""
    try:
        from django.contrib.auth.models import User
        from .models import Inventario, UsuarioInventario
        
        resultado = []
        
        # Eliminar admin y test si existen
        User.objects.filter(username='admin@email.com').delete()
        User.objects.filter(username='test@email.com').delete()
        resultado.append("✅ Admin y test eliminados (si existían)")
        
        # Crear admin
        User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
        resultado.append("✅ Admin creado: admin@email.com / admin123")
        
        # Crear test
        User.objects.create_user('test@email.com', 'test@email.com', '1234')
        resultado.append("✅ Test creado: test@email.com / 1234")
        
        # Crear inventario Test
        inv_test, _ = Inventario.objects.get_or_create(nombre='Test')
        resultado.append("✅ Inventario Test creado")
        
        # Asignar test a su inventario
        user_test = User.objects.get(username='test@email.com')
        if not UsuarioInventario.objects.filter(usuario=user_test).exists():
            UsuarioInventario.objects.create(usuario=user_test, inventario=inv_test)
            resultado.append("✅ Relación test-inventario creada")
        
        resultado.append("")
        resultado.append("📋 CREDENCIALES:")
        resultado.append("   admin@email.com / admin123")
        resultado.append("   test@email.com / 1234")
        
        html = "<h1>🚀 Admin y test creados exitosamente</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al login</a>"
        
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")

# ================= RESETEAR ADMIN =================
def resetear_admin(request):
    """Resetea el admin y test completamente"""
    try:
        resultado = []
        resultado.append("🔄 RESETEANDO ADMIN Y TEST")
        resultado.append("="*50)
        
        # Eliminar admin y test
        User.objects.filter(username='admin@email.com').delete()
        User.objects.filter(username='test@email.com').delete()
        resultado.append("✅ Admin y test eliminados")
        
        # Crear admin
        User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
        resultado.append("✅ Admin creado: admin@email.com / admin123")
        
        # Crear test
        User.objects.create_user('test@email.com', 'test@email.com', '1234')
        resultado.append("✅ Test creado: test@email.com / 1234")
        
        # Crear inventario Test
        inv_test, _ = Inventario.objects.get_or_create(nombre='Test')
        resultado.append("✅ Inventario Test creado")
        
        # Asignar test a su inventario
        user_test = User.objects.get(username='test@email.com')
        if not UsuarioInventario.objects.filter(usuario=user_test).exists():
            UsuarioInventario.objects.create(usuario=user_test, inventario=inv_test)
            resultado.append("✅ Relación test-inventario creada")
        
        resultado.append("="*50)
        resultado.append("✅ ADMIN Y TEST RESETEADOS!")
        
        html = "<h1>🔄 Admin y test reseteados</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al login</a>"
        
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")

def forzar_static(request):
    """Fuerza la recarga de archivos estáticos"""
    import subprocess
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'collectstatic', '--noinput', '--clear'],
            capture_output=True,
            text=True,
            cwd='/opt/render/project/src'
        )
        return HttpResponse(f"<pre>{result.stdout}</pre>")
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}")

def reparar_usuarios_y_inventarios(request):
    """Repara todos los usuarios sin inventario y crea admin si no existe"""
    try:
        from django.contrib.auth.models import User
        from django.http import HttpResponse
        from .models import UsuarioInventario, Inventario
        
        resultado = []
        resultado.append("🔧 REPARANDO USUARIOS E INVENTARIOS")
        resultado.append("="*50)
        
        # ========== 1. CREAR ADMIN SI NO EXISTE ==========
        if not User.objects.filter(username='admin@email.com').exists():
            User.objects.create_superuser('admin@email.com', 'admin@email.com', 'admin123')
            resultado.append("✅ Admin creado: admin@email.com / admin123")
        else:
            admin = User.objects.get(username='admin@email.com')
            if not admin.is_superuser:
                admin.is_superuser = True
                admin.is_staff = True
                admin.save()
            resultado.append("✅ Admin ya existe")
        
        # ========== 2. VERIFICAR INVENTARIO DEL ADMIN ==========
        admin = User.objects.get(username='admin@email.com')
        if not UsuarioInventario.objects.filter(usuario=admin).exists():
            inv_principal, _ = Inventario.objects.get_or_create(nombre='Principal')
            UsuarioInventario.objects.create(usuario=admin, inventario=inv_principal)
            resultado.append("✅ Inventario Principal asignado a admin")
        
        # ========== 3. REPARAR TODOS LOS USUARIOS ==========
        for user in User.objects.all():
            try:
                perfil = UsuarioInventario.objects.get(usuario=user)
                resultado.append(f"✅ {user.email} -> {perfil.inventario.nombre}")
            except UsuarioInventario.DoesNotExist:
                resultado.append(f"⚠️ {user.email} -> Creando inventario...")
                inventario = Inventario.objects.create(nombre=f"Inventario de {user.email}")
                UsuarioInventario.objects.create(usuario=user, inventario=inventario)
                resultado.append(f"✅ {user.email} -> {inventario.nombre} creado")
        
        # ========== 4. CREAR TEST SI NO EXISTE ==========
        if not User.objects.filter(username='test@email.com').exists():
            user = User.objects.create_user('test@email.com', 'test@email.com', '1234')
            resultado.append("✅ Test creado: test@email.com / 1234")
            inv_test, _ = Inventario.objects.get_or_create(nombre='Test')
            UsuarioInventario.objects.create(usuario=user, inventario=inv_test)
            resultado.append("✅ Inventario Test asignado")
        else:
            user = User.objects.get(username='test@email.com')
            if not UsuarioInventario.objects.filter(usuario=user).exists():
                inv_test, _ = Inventario.objects.get_or_create(nombre='Test')
                UsuarioInventario.objects.create(usuario=user, inventario=inv_test)
                resultado.append("✅ Inventario Test asignado a test")
        
        # ========== 5. CREAR TIENDAS ==========
        tiendas = [
            {"nombre": "Repmotos", "email": "repmotos@email.com", "password": "123456"},
            {"nombre": "MotoPartes SAS", "email": "motopartes@email.com", "password": "mp2024"},
            {"nombre": "Rapimotos", "email": "rapimotos@email.com", "password": "rapi123"},
            {"nombre": "Motorepuestos Plus", "email": "motoplus@email.com", "password": "plus2024"},
        ]
        
        for tienda in tiendas:
            if not User.objects.filter(username=tienda['email']).exists():
                user = User.objects.create_user(tienda['email'], tienda['email'], tienda['password'])
                resultado.append(f"✅ {tienda['email']} / {tienda['password']}")
            else:
                user = User.objects.get(username=tienda['email'])
                resultado.append(f"✅ {tienda['email']} ya existe")
            
            # Verificar inventario
            inv, _ = Inventario.objects.get_or_create(nombre=tienda['nombre'])
            if not UsuarioInventario.objects.filter(usuario=user).exists():
                UsuarioInventario.objects.create(usuario=user, inventario=inv)
                resultado.append(f"   📦 Inventario {tienda['nombre']} asignado")
        
        # ========== 6. MOSTRAR TODOS LOS USUARIOS ==========
        resultado.append("")
        resultado.append("📋 USUARIOS REGISTRADOS:")
        for u in User.objects.all():
            es_admin = "👑 Admin" if u.is_superuser else "👤 Usuario"
            try:
                inv = UsuarioInventario.objects.get(usuario=u)
                resultado.append(f"   {u.email} - {es_admin} - {inv.inventario.nombre}")
            except:
                resultado.append(f"   {u.email} - {es_admin} - Sin inventario")
        
        resultado.append("="*50)
        resultado.append("✅ REPARACIÓN COMPLETADA")
        
        html = "<h1>🔧 Reparación completada</h1>"
        html += "<div style='font-family: monospace; background: #f0f0f0; padding: 20px; border-radius: 10px;'>"
        for line in resultado:
            html += f"<p>{line}</p>"
        html += "</div>"
        html += "<br><a href='/login/' style='padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Ir al login</a>"
        
        return HttpResponse(html)
        
    except Exception as e:
        import traceback
        return HttpResponse(f"❌ Error: {str(e)}<br><br><pre>{traceback.format_exc()}</pre>")
