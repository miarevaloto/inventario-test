from flask import Flask, render_template, request, redirect, session, flash, send_file, jsonify
from reportlab.platypus import SimpleDocTemplate, Table
import sqlite3
import io
import os
import sys
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret_key_for_render_production")

# ================= DB =================
def get_db():
    db_path = os.path.join(os.getcwd(), 'inventario.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if cur.fetchone():
            conn.close()
            # AGREGADO: Reparar estructura incluso si ya existe
            repair_db()
            return True

        # Crear tablas
        cur.execute("""CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'usuario',
            nombre TEXT,
            inventario_id INTEGER
        )""")
        cur.execute("CREATE TABLE inventarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL)")
        cur.execute("""CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL,
            inventario_id INTEGER NOT NULL
        )""")
        cur.execute("""CREATE TABLE ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            producto TEXT,
            cantidad INTEGER,
            precio REAL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            inventario_id INTEGER
        )""")

        # Datos de prueba
        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", ("Principal",))
        inv_principal_id = cur.lastrowid
        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", ("Repmotos",))
        inv_repmotos_id = cur.lastrowid

        cur.execute("INSERT INTO usuarios (email,password,rol,nombre,inventario_id) VALUES (?,?,?,?,?)",
                    ("admin@email.com","admin123","admin","Administrador",inv_principal_id))
        cur.execute("INSERT INTO usuarios (email,password,rol,nombre,inventario_id) VALUES (?,?,?,?,?)",
                    ("repmotos@email.com","123456","usuario","Repuestos Motos",inv_repmotos_id))
        cur.execute("INSERT INTO usuarios (email,password,rol,nombre,inventario_id) VALUES (?,?,?,?,?)",
                    ("test@email.com","","usuario","Usuario Test",inv_principal_id))

        # Productos para repmotos
        productos = [
            ("Aceite 4T", "Lubricantes", 65, 25000.0),
            ("Filtro de aire", "Repuestos", 20, 15000.0),
            ("Bujía NGK", "Repuestos", 20, 10000.0),
            ("Casco integral", "Accesorios", 15, 120000.0),
            ("Guantes moto", "Accesorios", 25, 30000.0),
            ("Cadena moto", "Transmisión", 20, 80000.0),
            ("Kit arrastre", "Transmisión", 10, 150000.0),
            ("Llanta delantera", "Llantas", 18, 90000.0),
            ("Llanta trasera", "Llantas", 15, 110000.0),
            ("Pastillas de freno", "Frenos", 35, 20000.0)
        ]
        
        for nombre, categoria, cantidad, precio in productos:
            cur.execute("""
                INSERT INTO productos (nombre, categoria, cantidad, precio, inventario_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, categoria, cantidad, precio, inv_repmotos_id))

        conn.commit()
        conn.close()
        
        # AGREGADO: Reparar estructura
        repair_db()
        
        return True
    except Exception as e:
        print(f"❌ Error en init_db: {str(e)}", file=sys.stderr)
        return False


# ================= REPARAR BASE DE DATOS =================
def repair_db():
    """Repara la estructura de la base de datos - Agrega columnas faltantes"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Verificar tabla ventas
        cur.execute("PRAGMA table_info(ventas)")
        columnas = [col[1] for col in cur.fetchall()]
        
        print(f"📋 Columnas en ventas: {columnas}", file=sys.stderr)
        
        # Agregar columna precio si no existe
        if 'precio' not in columnas:
            print("📝 Agregando columna 'precio' a ventas...", file=sys.stderr)
            cur.execute("ALTER TABLE ventas ADD COLUMN precio REAL DEFAULT 0")
            print("✅ Columna 'precio' agregada", file=sys.stderr)
        
        # Agregar columna producto si no existe
        if 'producto' not in columnas:
            print("📝 Agregando columna 'producto' a ventas...", file=sys.stderr)
            cur.execute("ALTER TABLE ventas ADD COLUMN producto TEXT DEFAULT ''")
            print("✅ Columna 'producto' agregada", file=sys.stderr)
        
        # Agregar columna fecha si no existe
        if 'fecha' not in columnas:
            print("📝 Agregando columna 'fecha' a ventas...", file=sys.stderr)
            cur.execute("ALTER TABLE ventas ADD COLUMN fecha TEXT DEFAULT CURRENT_TIMESTAMP")
            print("✅ Columna 'fecha' agregada", file=sys.stderr)
        
        # Agregar columna inventario_id si no existe
        if 'inventario_id' not in columnas:
            print("📝 Agregando columna 'inventario_id' a ventas...", file=sys.stderr)
            cur.execute("ALTER TABLE ventas ADD COLUMN inventario_id INTEGER DEFAULT 0")
            print("✅ Columna 'inventario_id' agregada", file=sys.stderr)
        
        conn.commit()
        conn.close()
        print("✅ Base de datos reparada exitosamente", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Error reparando BD: {str(e)}", file=sys.stderr)
        return False


# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        if request.is_json:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
        else:
            email = request.form.get("email")
            password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuarios WHERE email=? AND password=?", (email,password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["rol"] = user["rol"]
            session["inventario_id"] = user["inventario_id"]

            return {"ok": True, "redirect": "/admin" if user["rol"] == "admin" else "/index"} \
                if request.is_json else redirect("/admin" if user["rol"] == "admin" else "/index")

        return {"ok": False, "msg": "Credenciales incorrectas"}

    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":

        if request.is_json:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
        else:
            email = request.form.get("email")
            password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        if cur.fetchone():
            conn.close()
            return {"ok": False, "msg": "Usuario ya existe"}

        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (f"Inventario de {email}",))
        inventario_id = cur.lastrowid

        cur.execute("""
        INSERT INTO usuarios (email,password,rol,inventario_id)
        VALUES (?,?, 'usuario',?)
        """,(email,password,inventario_id))

        conn.commit()
        conn.close()

        return {"ok": True}

    return render_template("register.html")


# ================= HEALTH =================
@app.route("/health")
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM usuarios")
        total_usuarios = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) as total FROM productos")
        total_productos = cur.fetchone()["total"]
        conn.close()
        
        return jsonify({
            "status": "ok",
            "usuarios": total_usuarios,
            "productos": total_productos
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ================= INDEX =================
@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("rol") == "admin":
        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()

    cur.execute("SELECT DISTINCT categoria FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    categorias = cur.fetchall()
    
    total_valor = 0
    for p in productos:
        total_valor += p["cantidad"] * p["precio"]

    conn.close()

    return render_template("index.html", productos=productos, categorias=categorias, 
                         total_valor=total_valor, producto_buscado=None)


# ================= BUSCAR PRODUCTO =================
@app.route("/buscar_producto", methods=["POST"])
def buscar_producto():
    if "user_id" not in session:
        return redirect("/login")

    try:
        producto_id = int(request.form["id"])
    except:
        flash("❌ ID inválido")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE id=? AND inventario_id=?", (producto_id, session["inventario_id"]))
    producto = cur.fetchone()

    if not producto:
        conn.close()
        flash("❌ Producto no encontrado")
        return redirect("/index")

    cur.execute("SELECT * FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()

    cur.execute("SELECT DISTINCT categoria FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    categorias = cur.fetchall()
    
    total_valor = 0
    for p in productos:
        total_valor += p["cantidad"] * p["precio"]

    conn.close()

    return render_template("index.html", productos=productos, categorias=categorias, 
                         producto_buscado=producto, total_valor=total_valor)


# ================= AGREGAR PRODUCTO =================
@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():
    if "user_id" not in session:
        return redirect("/login")

    try:
        precio = float(request.form["precio"])
        cantidad = int(request.form["cantidad"])
    except:
        flash("❌ Datos inválidos")
        return redirect("/index")

    if precio <= 0 or cantidad <= 0:
        flash("❌ Valores inválidos")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO productos (nombre, categoria, precio, cantidad, inventario_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.form["nombre"],
        request.form["categoria"],
        precio,
        cantidad,
        session["inventario_id"]
    ))

    conn.commit()
    conn.close()

    flash("✅ Producto agregado")
    return redirect("/index")

# ================= ELIMINAR PRODUCTO =================
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))
    conn.commit()
    conn.close()
    
    flash("✅ Producto eliminado")
    return redirect("/index")


# ================= SUMAR STOCK =================
@app.route("/sumar/<int:id>", methods=["POST"])
def sumar(id):
    if "user_id" not in session:
        return redirect("/login")

    try:
        cantidad = int(request.form["cantidad"])
    except:
        flash("❌ Cantidad inválida")
        return redirect("/index")

    if cantidad <= 0:
        flash("❌ Cantidad inválida")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE productos
    SET cantidad = cantidad + ?
    WHERE id=? AND inventario_id=?
    """, (cantidad, id, session["inventario_id"]))

    conn.commit()
    conn.close()

    flash("✅ Stock actualizado")
    return redirect("/index")


# ================= VENDER DESDE INDEX =================
@app.route("/vender/<int:id>", methods=["POST"])
def vender(id):
    if "user_id" not in session:
        return redirect("/login")

    try:
        cantidad = int(request.form["cantidad"])
    except:
        flash("❌ Datos inválidos")
        return redirect("/index")

    if cantidad <= 0:
        flash("❌ Cantidad inválida")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))
    producto = cur.fetchone()

    if not producto or cantidad > producto["cantidad"]:
        conn.close()
        flash("❌ Error en venta")
        return redirect("/index")

    cur.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id=?", (cantidad,id))
    cur.execute("INSERT INTO ventas (producto_id,cantidad) VALUES (?,?)", (id,cantidad))

    conn.commit()
    conn.close()

    flash("✅ Venta realizada")
    return redirect("/index")


# ================= VENTAS =================
@app.route("/ventas")
def ventas():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()

    cur.execute("""
        SELECT v.id, p.nombre as producto, v.cantidad
        FROM ventas v
        JOIN productos p ON v.producto_id = p.id
        WHERE p.inventario_id=?
        ORDER BY v.id DESC
    """, (session["inventario_id"],))
    ventas = cur.fetchall()

    conn.close()

    return render_template("ventas.html", productos=productos, ventas=ventas)


# ================= REGISTRAR VENTA =================
@app.route("/venta", methods=["POST"])
def venta():
    if "user_id" not in session:
        return redirect("/login")

    try:
        producto_id = int(request.form["producto_id"])
        cantidad = int(request.form["cantidad"])
    except:
        flash("❌ Datos inválidos")
        return redirect("/ventas")

    if cantidad <= 0:
        flash("❌ Cantidad inválida")
        return redirect("/ventas")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE id=? AND inventario_id=?", (producto_id, session["inventario_id"]))
    producto = cur.fetchone()

    if not producto or cantidad > producto["cantidad"]:
        conn.close()
        flash("❌ Error en venta")
        return redirect("/ventas")

    cur.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id=?", (cantidad, producto_id))
    cur.execute("INSERT INTO ventas (producto_id, cantidad) VALUES (?, ?)", (producto_id, cantidad))

    conn.commit()
    conn.close()

    flash("✅ Venta registrada")
    return redirect("/ventas")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    total_productos = cur.fetchone()["total"]

    cur.execute("SELECT SUM(cantidad) as stock FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    stock_total = cur.fetchone()["stock"] or 0

    cur.execute("""
    SELECT SUM(v.cantidad * p.precio) as ventas
    FROM ventas v
    JOIN productos p ON v.producto_id = p.id
    WHERE p.inventario_id=?
    """, (session["inventario_id"],))
    ventas_total = cur.fetchone()["ventas"] or 0

    cur.execute("""
    SELECT p.nombre, SUM(v.cantidad) as vendidos
    FROM ventas v
    JOIN productos p ON v.producto_id = p.id
    WHERE p.inventario_id=?
    GROUP BY p.id
    ORDER BY vendidos DESC
    LIMIT 5
    """, (session["inventario_id"],))
    top_productos = cur.fetchall()

    conn.close()

    return render_template("dashboard.html",
        total_productos=total_productos,
        stock_total=stock_total,
        ventas_total=ventas_total,
        top_productos=top_productos
    )

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("rol") != "admin":
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()

    cur.execute("SELECT * FROM inventarios")
    inventarios = cur.fetchall()

    conn.close()

    return render_template("admin.html", usuarios=usuarios, inventarios=inventarios)


# ================= CREAR USUARIO ADMIN =================
@app.route("/crear_usuario_admin", methods=["POST"])
def crear_usuario_admin():
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect("/login")
    
    nombre = request.form["nombre"]
    email = request.form["email"]
    password = request.form["password"]
    rol = request.form["rol"]
    inventario_id = request.form["inventario_id"]
    nuevo_inventario = request.form.get("nuevo_inventario", "")
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        if inventario_id == "nuevo" and nuevo_inventario:
            cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (nuevo_inventario,))
            inventario_id = cur.lastrowid
        
        cur.execute("""
            INSERT INTO usuarios (nombre, email, password, rol, inventario_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, email, password, rol, inventario_id))
        conn.commit()
        flash("✅ Usuario creado exitosamente")
    except sqlite3.IntegrityError:
        flash("❌ El correo ya está registrado")
    finally:
        conn.close()
    
    return redirect("/admin")


# ================= ASIGNAR INVENTARIO =================
@app.route("/asignar", methods=["POST"])
def asignar_inventario():
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect("/login")
    
    user_id = request.form["user_id"]
    inventario_id = request.form["inventario_id"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET inventario_id=? WHERE id=?", (inventario_id, user_id))
    conn.commit()
    conn.close()
    
    flash("✅ Inventario asignado correctamente")
    return redirect("/admin")


# ================= CREAR INVENTARIO =================
@app.route("/crear_inventario", methods=["POST"])
def crear_inventario():
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect("/login")
    
    nombre = request.form["nombre"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()
    
    flash(f"✅ Inventario '{nombre}' creado exitosamente")
    return redirect("/admin")


# ================= MODIFICAR INVENTARIO =================
@app.route("/modificar_inventario", methods=["POST"])
def modificar_inventario():
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect("/login")
    
    inventario_id = request.form["id"]
    nombre = request.form["nombre"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE inventarios SET nombre=? WHERE id=?", (nombre, inventario_id))
    conn.commit()
    conn.close()
    
    flash("✅ Inventario modificado exitosamente")
    return redirect("/admin")


# ================= ELIMINAR INVENTARIO =================
@app.route("/eliminar_inventario", methods=["POST"])
def eliminar_inventario():
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect("/login")
    
    inventario_id = request.form["id"]
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) as total FROM productos WHERE inventario_id=?", (inventario_id,))
        total = cur.fetchone()["total"]
        
        if total > 0:
            flash(f"❌ No se puede eliminar el inventario porque tiene {total} productos")
            conn.close()
            return redirect("/admin")
        
        cur.execute("DELETE FROM inventarios WHERE id=?", (inventario_id,))
        conn.commit()
        flash("✅ Inventario eliminado exitosamente")
    except Exception as e:
        conn.rollback()
        flash("❌ Error al eliminar inventario")
    finally:
        conn.close()
    
    return redirect("/admin")


# ================= ELIMINAR USUARIO =================
@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if id == session["user_id"]:
        flash("❌ No puedes eliminarte")
        conn.close()
        return redirect("/admin")

    cur.execute("SELECT inventario_id, email FROM usuarios WHERE id=?", (id,))
    user = cur.fetchone()

    if user:
        cur.execute("SELECT COUNT(*) as total FROM usuarios WHERE inventario_id=?", (user["inventario_id"],))
        otros = cur.fetchone()["total"]
        
        if otros <= 1:
            cur.execute("DELETE FROM productos WHERE inventario_id=?", (user["inventario_id"],))
            cur.execute("DELETE FROM inventarios WHERE id=?", (user["inventario_id"],))

    cur.execute("DELETE FROM usuarios WHERE id=?", (id,))

    conn.commit()
    conn.close()

    flash("✅ Usuario eliminado")
    return redirect("/admin")


# ================= REPORTE PDF =================
@app.route("/reporte_pdf")
def reporte_pdf():
    if "user_id" not in session:
        return redirect("/login")

    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from reportlab.lib import colors
        from reportlab.lib.units import inch, cm
        from datetime import datetime
        import os
        
        # Crear buffer y documento en horizontal para mejor visualización
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), 
                                leftMargin=0.5*inch, rightMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Estilos personalizados
        styles = getSampleStyleSheet()
        
        # Estilo para título principal
        titulo_style = ParagraphStyle(
            'TituloStyle',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.HexColor('#1a4d8c'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulo
        subtitulo_style = ParagraphStyle(
            'SubtituloStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4a4a4a'),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        # Estilo para información de empresa
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=5
        )
        
        # Estilo para encabezados de sección
        seccion_style = ParagraphStyle(
            'SeccionStyle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1a4d8c'),
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para tarjetas de resumen
        resumen_style = ParagraphStyle(
            'ResumenStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER
        )
        
        # Lista para almacenar elementos del PDF
        story = []
        
        # ================= ENCABEZADO =================
        # Título principal
        story.append(Paragraph("📦 REPORTE DE INVENTARIO", titulo_style))
        story.append(Spacer(1, 5))
        
        # Información de la empresa
        story.append(Paragraph("Sistema de Gestión de Inventarios", subtitulo_style))
        story.append(Spacer(1, 5))
        
        # Fecha y usuario
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nombre_usuario = session.get('nombre', session.get('email', 'Usuario'))
        
        story.append(Paragraph(f"Generado por: {nombre_usuario}", info_style))
        story.append(Paragraph(f"Fecha de emisión: {fecha_actual}", info_style))
        story.append(Spacer(1, 20))
        
        # ================= LÍNEA SEPARADORA =================
        story.append(Paragraph("<hr color='#1a4d8c'/>", styles['Normal']))
        story.append(Spacer(1, 15))
        
        # ================= CONEXIÓN A BD =================
        conn = get_db()
        cur = conn.cursor()
        
        # ================= TARJETAS DE RESUMEN =================
        story.append(Paragraph("📊 RESUMEN GENERAL", seccion_style))
        
        # Obtener estadísticas
        cur.execute("SELECT COUNT(*) as total FROM productos WHERE inventario_id=?", (session["inventario_id"],))
        total_productos = cur.fetchone()["total"] or 0
        
        cur.execute("SELECT SUM(cantidad) as total FROM productos WHERE inventario_id=?", (session["inventario_id"],))
        stock_total = cur.fetchone()["total"] or 0
        
        cur.execute("SELECT SUM(cantidad * precio) as total FROM productos WHERE inventario_id=?", (session["inventario_id"],))
        valor_total = cur.fetchone()["total"] or 0
        
        cur.execute("SELECT COUNT(DISTINCT categoria) as total FROM productos WHERE inventario_id=?", (session["inventario_id"],))
        total_categorias = cur.fetchone()["total"] or 0
        
        # Crear tabla de resumen estilo tarjetas
        resumen_data = [
            ["📦 Total Productos", "📊 Stock Total", "💰 Valor Inventario", "📂 Categorías"],
            [f"{total_productos:,}", f"{stock_total:,} und.", f"${valor_total:,.2f}", f"{total_categorias}"]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d8c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e8f0fe')),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#1a4d8c')),
            ('FONTSIZE', (0, 1), (-1, 1), 16),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 1), (-1, 1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 15),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c0c0c0')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1a4d8c')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(resumen_table)
        story.append(Spacer(1, 20))
        
        # ================= INFORMACIÓN DEL INVENTARIO =================
        story.append(Paragraph("📋 LISTADO DE PRODUCTOS", seccion_style))
        
        # Obtener productos del inventario del usuario
        cur.execute("""
            SELECT id, nombre, categoria, cantidad, precio, (cantidad * precio) as valor_total
            FROM productos 
            WHERE inventario_id=?
            ORDER BY categoria, nombre
        """, (session["inventario_id"],))
        
        products = cur.fetchall()
        
        if products:
            # Preparar datos para la tabla
            data = [["ID", "Producto", "Categoría", "Cantidad", "Precio Unit.", "Valor Total"]]
            
            total_general = 0
            for row in products:
                valor = row["cantidad"] * row["precio"]
                total_general += valor
                
                # Colores según stock bajo
                cantidad_text = str(row["cantidad"])
                if row["cantidad"] < 5:
                    cantidad_text = f"⚠️ {row['cantidad']}"
                
                data.append([
                    row["id"],
                    row["nombre"],
                    row["categoria"],
                    cantidad_text,
                    f"${row['precio']:,.2f}",
                    f"${valor:,.2f}"
                ])
            
            # Agregar fila de total
            data.append(["", "", "", "", "TOTAL GENERAL:", f"${total_general:,.2f}"])
            
            # Crear tabla con estilos mejorados
            table = Table(data, colWidths=[0.6*inch, 2*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d8c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                
                # Filas de datos
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('ALIGN', (0, 1), (0, -2), 'CENTER'),
                ('ALIGN', (3, 1), (3, -2), 'CENTER'),
                ('ALIGN', (4, 1), (-1, -2), 'RIGHT'),
                ('VALIGN', (0, 1), (-1, -2), 'MIDDLE'),
                
                # Colores alternados para filas
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
                
                # Advertencia para stock bajo
                ('TEXTCOLOR', (3, 1), (3, -2), colors.HexColor('#dc3545'), lambda x, y: y >= 1 and data[y][3].startswith('⚠️')),
                
                # Total
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0fe')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 10),
                ('ALIGN', (4, -1), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (4, -1), (-1, -1), colors.HexColor('#1a4d8c')),
                
                # Bordes
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#cccccc')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a4d8c')),
            ]))
            
            story.append(table)
            
            # ================= RESULTADOS ADICIONALES =================
            story.append(Spacer(1, 20))
            story.append(Paragraph("📊 ANÁLISIS DE STOCK", seccion_style))
            
            # Productos con stock bajo
            cur.execute("""
                SELECT nombre, cantidad 
                FROM productos 
                WHERE inventario_id=? AND cantidad < 5
                ORDER BY cantidad ASC
                LIMIT 10
            """, (session["inventario_id"],))
            
            productos_bajos = cur.fetchall()
            
            if productos_bajos:
                bajo_data = [["Producto", "Stock Actual"]]
                for p in productos_bajos:
                    bajo_data.append([p["nombre"], str(p["cantidad"])])
                
                bajo_table = Table(bajo_data, colWidths=[3.5*inch, 1.5*inch])
                bajo_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')]),
                ]))
                
                story.append(Paragraph("⚠️ Productos con stock bajo (< 5 unidades):", styles['Normal']))
                story.append(Spacer(1, 5))
                story.append(bajo_table)
            else:
                story.append(Paragraph("✅ No hay productos con stock bajo", styles['Normal']))
            
            # ================= TOP PRODUCTOS =================
            story.append(Spacer(1, 20))
            story.append(Paragraph("🏆 TOP PRODUCTOS MÁS VENDIDOS", seccion_style))
            
            cur.execute("""
                SELECT producto, SUM(cantidad) as total_vendido
                FROM ventas
                WHERE inventario_id=? AND producto IS NOT NULL AND producto != ''
                GROUP BY producto
                ORDER BY total_vendido DESC
                LIMIT 10
            """, (session["inventario_id"],))
            
            top_ventas = cur.fetchall()
            
            if top_ventas:
                top_data = [["Producto", "Unidades Vendidas"]]
                for tv in top_ventas:
                    top_data.append([tv["producto"], str(tv["total_vendido"])])
                
                top_table = Table(top_data, colWidths=[3.5*inch, 1.5*inch])
                top_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fff4')]),
                ]))
                
                story.append(top_table)
            else:
                story.append(Paragraph("📭 No hay ventas registradas aún", styles['Normal']))
        
        else:
            story.append(Paragraph("📭 No hay productos registrados en este inventario", styles['Normal']))
        
        conn.close()
        
        # ================= PIE DE PÁGINA =================
        story.append(Spacer(1, 30))
        story.append(Paragraph("<hr color='#1a4d8c'/>", styles['Normal']))
        story.append(Spacer(1, 5))
        
        pie_style = ParagraphStyle(
            'PieStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("Este reporte es generado automáticamente por el Sistema de Gestión de Inventarios", pie_style))
        story.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}", pie_style))
        
        # ================= CONSTRUIR PDF =================
        doc.build(story)
        buffer.seek(0)
        
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_inventario_{timestamp}.pdf"
        
        return send_file(buffer, as_attachment=True, 
                        download_name=filename, 
                        mimetype='application/pdf')
    
    except Exception as e:
        print(f"❌ Error al generar PDF: {str(e)}", file=sys.stderr)
        flash(f"❌ Error al generar el reporte: {str(e)}")
        return redirect("/index")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= MAIN =================
if __name__ == "__main__":
    print("🚀 Iniciando aplicación...", file=sys.stderr)
    print("="*50, file=sys.stderr)
    
    init_db()
    
    print("\n" + "="*50, file=sys.stderr)
    print("🚀 APLICACIÓN INICIADA", file=sys.stderr)
    print("="*50, file=sys.stderr)
    print("🔐 CREDENCIALES:", file=sys.stderr)
    print("   admin@email.com / admin123", file=sys.stderr)
    print("   repmotos@email.com / 123456", file=sys.stderr)
    print("   test@email.com / cualquier contraseña", file=sys.stderr)
    print("="*50 + "\n", file=sys.stderr)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
