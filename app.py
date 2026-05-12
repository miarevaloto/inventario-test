from flask import Flask, render_template, request, redirect, session, flash, send_file, jsonify
import sqlite3
import os
import io
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tu_clave_secreta_aqui_cambiala_por_una_segura")

# ================= DECORADORES DE SEGURIDAD =================
def login_required(f):
    """Decorador para verificar que el usuario ha iniciado sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"ok": False, "msg": "No autorizado"}), 401
            flash("🔒 Por favor, inicia sesión para acceder a esta página", "warning")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorador para verificar roles de usuario"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("rol") != required_role:
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({"ok": False, "msg": "No tienes permisos"}), 403
                flash("⛔ No tienes permisos para acceder a esta página", "error")
                return redirect("/index")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ================= FUNCIONES BD =================
def get_db():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Verifica que la base de datos exista, pero NO modifica tus datos existentes"""
    conn = get_db()
    cur = conn.cursor()
    
    # Solo crear tablas si no existen (NO borra datos)
    cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'usuario',
        nombre TEXT,
        inventario_id INTEGER)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS inventarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL,
        iva REAL DEFAULT 0.19,
        descuento REAL DEFAULT 0,
        inventario_id INTEGER NOT NULL)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        producto TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL,
        fecha TEXT NOT NULL,
        inventario_id INTEGER NOT NULL)''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos SQLite verificada (tus datos existentes se conservan)")

# ================= RUTAS DE AUTENTICACIÓN =================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/index")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    # POST - Login con AJAX
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"ok": False, "msg": "Correo y contraseña requeridos"})
    
    conn = get_db()
    cur = conn.cursor()
    
    # Buscar usuario - COMPARACIÓN DIRECTA (texto plano como está en tu BD)
    cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
    user = cur.fetchone()
    
    if user:
        # Comparación directa de contraseñas (sin hash)
        if user["password"] == password:
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session["rol"] = user["rol"]
            session["nombre"] = user.get("nombre", user["email"])
            session["inventario_id"] = user["inventario_id"]
            conn.close()
            print(f"✅ Login exitoso: {email}")
            return jsonify({"ok": True, "redirect": "/index"})
        else:
            # Para test@email.com que tiene contraseña vacía
            if email == "test@email.com":
                session["user_id"] = user["id"]
                session["email"] = user["email"]
                session["rol"] = user["rol"]
                session["nombre"] = user.get("nombre", user["email"])
                session["inventario_id"] = user["inventario_id"]
                conn.close()
                print(f"✅ Login exitoso (usuario test): {email}")
                return jsonify({"ok": True, "redirect": "/index"})
    
    conn.close()
    print(f"❌ Login fallido: {email}")
    return jsonify({"ok": False, "msg": "Credenciales incorrectas"})

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    # POST - Register con AJAX
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"ok": False, "msg": "Correo y contraseña requeridos"})
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Asignar inventario por defecto
        cur.execute("SELECT id FROM inventarios LIMIT 1")
        inv_row = cur.fetchone()
        if inv_row:
            inv_id = inv_row[0]
        else:
            cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", ("Principal",))
            inv_id = cur.lastrowid
        
        # Guardar contraseña en texto plano (como en tu BD existente)
        cur.execute("""
            INSERT INTO usuarios (email, password, rol, nombre, inventario_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (email, password, "usuario", email.split('@')[0], inv_id))
        conn.commit()
        print(f"✅ Nuevo usuario registrado: {email}")
        return jsonify({"ok": True, "msg": "Usuario creado exitosamente"})
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "msg": "El correo ya está registrado"})
    finally:
        conn.close()

# ================= RUTAS PRINCIPALES =================
@app.route("/index")
@login_required
def index():
    conn = get_db()
    cur = conn.cursor()
    
    # Obtener productos del inventario del usuario
    cur.execute("SELECT * FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()
    
    # Obtener categorías únicas
    cur.execute("SELECT DISTINCT categoria FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    categorias = cur.fetchall()
    
    # Calcular valor total del inventario
    total_valor = 0
    for p in productos:
        total_valor += p["cantidad"] * p["precio"]
    
    conn.close()
    
    return render_template("index.html", 
                         productos=productos, 
                         categorias=categorias,
                         producto_buscado=None,
                         total_valor=total_valor)

@app.route("/buscar_producto", methods=["POST"])
@login_required
def buscar_producto():
    producto_id = request.form["id"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos WHERE id=? AND inventario_id=?", 
                (producto_id, session["inventario_id"]))
    producto = cur.fetchone()
    
    # Obtener todos los productos para la tabla
    cur.execute("SELECT * FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()
    
    cur.execute("SELECT DISTINCT categoria FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    categorias = cur.fetchall()
    
    # Calcular valor total
    total_valor = 0
    for p in productos:
        total_valor += p["cantidad"] * p["precio"]
    
    conn.close()
    
    return render_template("index.html", 
                         productos=productos, 
                         categorias=categorias,
                         producto_buscado=producto,
                         total_valor=total_valor)

@app.route("/agregar_producto", methods=["POST"])
@login_required
def agregar_producto():
    nombre = request.form["nombre"]
    categoria_select = request.form["categoria_select"]
    nueva_categoria = request.form.get("nueva_categoria", "")
    cantidad = int(request.form["cantidad"])
    precio = float(request.form["precio"])
    
    # Determinar la categoría final
    if categoria_select == "nueva":
        categoria = nueva_categoria
    else:
        categoria = categoria_select
    
    if not categoria:
        flash("❌ Debes seleccionar o crear una categoría", "error")
        return redirect("/index")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO productos (nombre, categoria, cantidad, precio, inventario_id) 
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, categoria, cantidad, precio, session["inventario_id"]))
    conn.commit()
    conn.close()
    
    flash(f"✅ Producto '{nombre}' agregado exitosamente", "success")
    return redirect("/index")

@app.route("/delete/<int:id>")
@login_required
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))
    conn.commit()
    conn.close()
    
    flash("🗑️ Producto eliminado correctamente", "success")
    return redirect("/index")

@app.route("/sumar/<int:id>", methods=["POST"])
@login_required
def sumar(id):
    cantidad = int(request.form["cantidad"])
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE productos 
        SET cantidad = cantidad + ? 
        WHERE id=? AND inventario_id=?
    """, (cantidad, id, session["inventario_id"]))
    conn.commit()
    conn.close()
    
    flash(f"✅ Se agregaron {cantidad} unidades al stock", "success")
    return redirect("/index")

@app.route("/vender/<int:id>", methods=["POST"])
@login_required
def vender(id):
    cantidad = int(request.form["cantidad"])
    
    conn = get_db()
    cur = conn.cursor()
    
    # Verificar stock suficiente
    cur.execute("SELECT * FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))
    producto = cur.fetchone()
    
    if not producto:
        flash("❌ Producto no encontrado", "error")
        conn.close()
        return redirect("/index")
    
    if producto["cantidad"] < cantidad:
        flash(f"❌ Stock insuficiente. Solo hay {producto['cantidad']} unidades", "error")
        conn.close()
        return redirect("/index")
    
    # Actualizar stock
    cur.execute("""
        UPDATE productos 
        SET cantidad = cantidad - ? 
        WHERE id=? AND inventario_id=?
    """, (cantidad, id, session["inventario_id"]))
    
    # Registrar venta
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO ventas (producto_id, producto, cantidad, precio, fecha, inventario_id) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (id, producto["nombre"], cantidad, producto["precio"], fecha, session["inventario_id"]))
    
    conn.commit()
    conn.close()
    
    flash(f"💰 Venta realizada: {cantidad} x {producto['nombre']}", "success")
    return redirect("/index")

# ================= ADMIN =================
@app.route("/admin")
@login_required
@role_required("admin")
def admin():
    conn = get_db()
    cur = conn.cursor()
    
    # Obtener usuarios
    cur.execute("SELECT * FROM usuarios ORDER BY id")
    usuarios = cur.fetchall()
    
    # Obtener inventarios
    cur.execute("SELECT * FROM inventarios ORDER BY id")
    inventarios = cur.fetchall()
    
    # Contar productos por inventario
    for inv in inventarios:
        cur.execute("SELECT COUNT(*) as total FROM productos WHERE inventario_id=?", (inv["id"],))
        inv["total_productos"] = cur.fetchone()["total"]
    
    conn.close()
    
    return render_template("admin.html", 
                         usuarios=usuarios, 
                         inventarios=inventarios)

@app.route("/crear_usuario_admin", methods=["POST"])
@login_required
@role_required("admin")
def crear_usuario_admin():
    nombre = request.form["nombre"]
    email = request.form["email"]
    password = request.form["password"]
    rol = request.form["rol"]
    inventario_id = request.form["inventario_id"]
    nuevo_inventario = request.form.get("nuevo_inventario", "")
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Si se crea nuevo inventario
        if inventario_id == "nuevo" and nuevo_inventario:
            cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (nuevo_inventario,))
            inventario_id = cur.lastrowid
        
        # Guardar contraseña en texto plano
        cur.execute("""
            INSERT INTO usuarios (nombre, email, password, rol, inventario_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, email, password, rol, inventario_id))
        conn.commit()
        flash(f"✅ Usuario '{email}' creado exitosamente", "success")
    except sqlite3.IntegrityError:
        flash("❌ El correo ya está registrado", "error")
    finally:
        conn.close()
    
    return redirect("/admin")

@app.route("/asignar", methods=["POST"])
@login_required
@role_required("admin")
def asignar_inventario():
    user_id = request.form["user_id"]
    inventario_id = request.form["inventario_id"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET inventario_id=? WHERE id=?", (inventario_id, user_id))
    conn.commit()
    conn.close()
    
    flash("✅ Inventario asignado correctamente", "success")
    return redirect("/admin")

@app.route("/eliminar_usuario/<int:id>")
@login_required
@role_required("admin")
def eliminar_usuario(id):
    if id == session["user_id"]:
        flash("❌ No puedes eliminarte a ti mismo", "error")
        return redirect("/admin")
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT inventario_id, nombre, email FROM usuarios WHERE id=?", (id,))
        user = cur.fetchone()
        
        if not user:
            flash("❌ Usuario no encontrado", "error")
            conn.close()
            return redirect("/admin")
        
        # Verificar si el inventario es usado por otros usuarios
        if user["inventario_id"]:
            cur.execute("SELECT COUNT(*) as total FROM usuarios WHERE inventario_id=? AND id != ?", 
                       (user["inventario_id"], id))
            otros_usuarios = cur.fetchone()["total"]
            
            if otros_usuarios == 0:  # Solo este usuario usa este inventario
                cur.execute("DELETE FROM productos WHERE inventario_id=?", (user["inventario_id"],))
                cur.execute("DELETE FROM inventarios WHERE id=?", (user["inventario_id"],))
        
        cur.execute("DELETE FROM usuarios WHERE id=?", (id,))
        conn.commit()
        flash(f"✅ Usuario '{user['email']}' eliminado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al eliminar usuario: {str(e)}", "error")
    finally:
        conn.close()
    
    return redirect("/admin")

@app.route("/crear_inventario", methods=["POST"])
@login_required
@role_required("admin")
def crear_inventario():
    nombre = request.form["nombre"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()
    
    flash(f"✅ Inventario '{nombre}' creado exitosamente", "success")
    return redirect("/admin")

@app.route("/modificar_inventario", methods=["POST"])
@login_required
@role_required("admin")
def modificar_inventario():
    inventario_id = request.form["id"]
    nombre = request.form["nombre"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE inventarios SET nombre=? WHERE id=?", (nombre, inventario_id))
    conn.commit()
    conn.close()
    
    flash(f"✅ Inventario modificado exitosamente", "success")
    return redirect("/admin")

@app.route("/eliminar_inventario", methods=["POST"])
@login_required
@role_required("admin")
def eliminar_inventario():
    inventario_id = request.form["id"]
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verificar si hay usuarios usando este inventario
        cur.execute("SELECT COUNT(*) as total FROM usuarios WHERE inventario_id=?", (inventario_id,))
        usuarios_usando = cur.fetchone()["total"]
        
        if usuarios_usando > 0:
            flash(f"❌ No se puede eliminar el inventario porque lo usan {usuarios_usando} usuario(s)", "error")
            conn.close()
            return redirect("/admin")
        
        # Verificar si el inventario tiene productos
        cur.execute("SELECT COUNT(*) as total FROM productos WHERE inventario_id=?", (inventario_id,))
        total = cur.fetchone()["total"]
        
        if total > 0:
            flash(f"❌ No se puede eliminar el inventario porque tiene {total} productos asociados", "error")
            conn.close()
            return redirect("/admin")
        
        cur.execute("DELETE FROM inventarios WHERE id=?", (inventario_id,))
        conn.commit()
        flash(f"✅ Inventario eliminado exitosamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al eliminar inventario", "error")
    finally:
        conn.close()
    
    return redirect("/admin")

# ================= DASHBOARD =================
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    
    # Total de productos
    cur.execute("SELECT COUNT(*) as total FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    total_productos = cur.fetchone()["total"]
    
    # Stock total
    cur.execute("SELECT SUM(cantidad) as total FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    stock_total = cur.fetchone()["total"] or 0
    
    # Ventas totales
    cur.execute("SELECT SUM(cantidad * precio) as total FROM ventas WHERE inventario_id=?", (session["inventario_id"],))
    ventas_total = cur.fetchone()["total"] or 0
    
    # Top productos más vendidos
    cur.execute("""
        SELECT producto, SUM(cantidad) as vendidos 
        FROM ventas 
        WHERE inventario_id=?
        GROUP BY producto 
        ORDER BY vendidos DESC 
        LIMIT 5
    """, (session["inventario_id"],))
    top_productos = cur.fetchall()
    
    conn.close()
    
    return render_template("dashboard.html", 
                         total_productos=total_productos,
                         stock_total=stock_total,
                         ventas_total=ventas_total,
                         top_productos=top_productos)

# ================= VENTAS =================
@app.route("/ventas")
@login_required
def ventas():
    conn = get_db()
    cur = conn.cursor()
    
    # Obtener productos para el selector
    cur.execute("SELECT id, nombre, cantidad, precio FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()
    
    # Obtener historial de ventas
    cur.execute("""
        SELECT v.* 
        FROM ventas v
        WHERE v.inventario_id=?
        ORDER BY v.id DESC
        LIMIT 50
    """, (session["inventario_id"],))
    ventas_list = cur.fetchall()
    
    conn.close()
    
    return render_template("ventas.html", 
                         productos=productos,
                         ventas=ventas_list)

@app.route("/venta", methods=["POST"])
@login_required
def registrar_venta():
    producto_id = request.form["producto_id"]
    cantidad = int(request.form["cantidad"])
    
    conn = get_db()
    cur = conn.cursor()
    
    # Verificar producto y stock
    cur.execute("SELECT * FROM productos WHERE id=? AND inventario_id=?", (producto_id, session["inventario_id"]))
    producto = cur.fetchone()
    
    if not producto:
        flash("❌ Producto no encontrado", "error")
        return redirect("/ventas")
    
    if producto["cantidad"] < cantidad:
        flash(f"❌ Stock insuficiente. Solo hay {producto['cantidad']} unidades", "error")
        return redirect("/ventas")
    
    # Actualizar stock
    cur.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id=?", (cantidad, producto_id))
    
    # Registrar venta
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO ventas (producto_id, producto, cantidad, precio, fecha, inventario_id) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (producto_id, producto["nombre"], cantidad, producto["precio"], fecha, session["inventario_id"]))
    
    conn.commit()
    conn.close()
    
    total = cantidad * producto["precio"]
    flash(f"💰 Venta registrada: {cantidad} x {producto['nombre']} = ${total:,.2f}", "success")
    return redirect("/ventas")

# ================= REPORTE PDF =================
@app.route("/reporte_pdf")
@login_required
def reporte_pdf():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            alignment=TA_CENTER,
            fontSize=16
        )
        
        story = []
        
        # Título
        story.append(Paragraph("Reporte de Inventario", title_style))
        story.append(Spacer(1, 12))
        
        # Fecha y usuario
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        story.append(Paragraph(f"Generado por: {session.get('nombre', 'Usuario')}", styles['Normal']))
        story.append(Paragraph(f"Fecha: {fecha}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        conn = get_db()
        cur = conn.cursor()
        
        # Obtener información del inventario
        cur.execute("""
            SELECT i.nombre as inventario_nombre, COUNT(p.id) as total_productos,
                   COALESCE(SUM(p.cantidad * p.precio), 0) as valor_total
            FROM inventarios i
            LEFT JOIN productos p ON i.id = p.inventario_id
            WHERE i.id = ?
            GROUP BY i.id
        """, (session["inventario_id"],))
        
        inventario_info = cur.fetchone()
        if inventario_info:
            story.append(Paragraph(f"Inventario: {inventario_info['inventario_nombre']}", styles['Normal']))
            story.append(Paragraph(f"Total Productos: {inventario_info['total_productos'] or 0}", styles['Normal']))
            story.append(Paragraph(f"Valor Total: ${inventario_info['valor_total']:,.2f}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Obtener productos
        cur.execute("""
            SELECT nombre, categoria, cantidad, precio, 
                   (cantidad * precio) as valor_total
            FROM productos
            WHERE inventario_id=?
            ORDER BY categoria, nombre
        """, (session["inventario_id"],))
        
        products = cur.fetchall()
        
        if products:
            data = [["Nombre", "Categoría", "Cantidad", "Precio Unitario", "Valor Total"]]
            
            total_general = 0
            for row in products:
                valor = row["cantidad"] * row["precio"]
                total_general += valor
                data.append([
                    row["nombre"], 
                    row["categoria"], 
                    f"{row['cantidad']:,}", 
                    f"${row['precio']:,.2f}", 
                    f"${valor:,.2f}"
                ])
            
            data.append(["", "", "", "TOTAL:", f"${total_general:,.2f}"])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -2), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph("No hay productos en este inventario", styles['Normal']))
        
        conn.close()
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(buffer, as_attachment=True, 
                        download_name=f"reporte_inventario_{datetime.now().strftime('%Y%m%d')}.pdf", 
                        mimetype='application/pdf')
    except Exception as e:
        flash(f"❌ Error al generar PDF: {str(e)}", "error")
        return redirect("/index")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= MAIN =================
if __name__ == "__main__":
    # Inicializar base de datos
    init_db()
    
    # Mostrar información de la base de datos
    conn = get_db()
    cur = conn.cursor()
    
    print("\n" + "="*50)
    print("📊 ESTADO DE LA BASE DE DATOS SQLITE")
    print("="*50)
    
    # Mostrar usuarios
    cur.execute("SELECT id, email, rol, inventario_id FROM usuarios")
    usuarios = cur.fetchall()
    print("\n👥 USUARIOS:")
    for u in usuarios:
        print(f"   ID: {u['id']} | Email: {u['email']} | Rol: {u['rol']} | Inventario ID: {u['inventario_id']}")
    
    # Mostrar inventarios
    cur.execute("SELECT id, nombre FROM inventarios")
    inventarios = cur.fetchall()
    print("\n📦 INVENTARIOS:")
    for inv in inventarios:
        cur.execute("SELECT COUNT(*) FROM productos WHERE inventario_id=?", (inv['id'],))
        num_productos = cur.fetchone()[0]
        print(f"   ID: {inv['id']} | Nombre: {inv['nombre']} | Productos: {num_productos}")
    
    # Mostrar productos
    cur.execute("SELECT COUNT(*) FROM productos")
    total_productos = cur.fetchone()[0]
    print(f"\n📦 TOTAL PRODUCTOS: {total_productos}")
    
    # Mostrar ventas
    cur.execute("SELECT COUNT(*) FROM ventas")
    total_ventas = cur.fetchone()[0]
    print(f"💰 TOTAL VENTAS REGISTRADAS: {total_ventas}")
    
    conn.close()
    
    print("\n" + "="*50)
    print("🚀 INICIANDO SERVIDOR")
    print("="*50)
    print("🔐 CREDENCIALES DE ACCESO:")
    print("   📧 admin@email.com")
    print("   🔑 Contraseña: admin123")
    print("   👑 Rol: Administrador")
    print("")
    print("   📧 repmotos@email.com")
    print("   🔑 Contraseña: 123456")
    print("   👤 Rol: Usuario")
    print("")
    print("   📧 test@email.com")
    print("   🔑 Contraseña: (cualquier texto o vacío)")
    print("   🧪 Rol: Usuario de prueba")
    print("="*50 + "\n")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
