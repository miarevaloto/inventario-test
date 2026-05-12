from flask import Flask, render_template, request, redirect, session, flash, send_file, jsonify
from reportlab.platypus import SimpleDocTemplate, Table
import sqlite3
import io
import os

app = Flask(__name__)
app.secret_key = "secret"


# ================= DB MODIFICADA PARA RENDER =================
def get_db():
    """Usa /tmp/inventario.db en Render para permitir escritura"""
    if os.environ.get("RENDER"):
        db_path = '/tmp/inventario.db'
    else:
        db_path = 'inventario.db'
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Crear tablas si no existen
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'usuario',
        nombre TEXT,
        inventario_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL,
        inventario_id INTEGER NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER,
        producto TEXT,
        cantidad INTEGER,
        precio REAL,
        fecha TEXT DEFAULT CURRENT_TIMESTAMP,
        inventario_id INTEGER
    )
    """)

    # Verificar si hay usuarios, si no, crear los de prueba
    cur.execute("SELECT COUNT(*) as total FROM usuarios")
    total = cur.fetchone()["total"]
    
    if total == 0:
        print("📝 Creando usuarios de prueba...")
        
        # Crear inventario principal
        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", ("Principal",))
        inv_principal_id = cur.lastrowid
        
        # Crear inventario para repmotos
        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", ("repmotos",))
        inv_repmotos_id = cur.lastrowid
        
        # Usuario Admin
        cur.execute("""
            INSERT INTO usuarios (email, password, rol, nombre, inventario_id) 
            VALUES (?, ?, ?, ?, ?)
        """, ("admin@email.com", "admin123", "admin", "Administrador", inv_principal_id))
        
        # Usuario Repmotos
        cur.execute("""
            INSERT INTO usuarios (email, password, rol, nombre, inventario_id) 
            VALUES (?, ?, ?, ?, ?)
        """, ("repmotos@email.com", "123456", "usuario", "Repuestos Motos", inv_repmotos_id))
        
        # Usuario Test (sin contraseña - permite cualquier cosa)
        cur.execute("""
            INSERT INTO usuarios (email, password, rol, nombre, inventario_id) 
            VALUES (?, ?, ?, ?, ?)
        """, ("test@email.com", "", "usuario", "Usuario Test", inv_principal_id))
        
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
        
        print(f"✅ Creados: 3 usuarios, 2 inventarios, {len(productos)} productos")

    conn.commit()
    conn.close()
    print("✅ Base de datos SQLite inicializada correctamente")


# ================= LOGIN (CORREGIDO - ENVÍA MENSAJES) =================
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

        # Buscar usuario por email
        cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        user = cur.fetchone()
        
        autenticado = False
        mensaje_error = "Credenciales incorrectas"
        
        if user:
            # Si es test@email.com, acepta cualquier contraseña
            if user["email"] == "test@email.com":
                autenticado = True
            # Si no, comparar contraseña directamente
            elif user["password"] == password:
                autenticado = True
            else:
                mensaje_error = "Contraseña incorrecta"
        else:
            mensaje_error = "Usuario no encontrado"
        
        conn.close()

        if autenticado:
            session["user_id"] = user["id"]
            session["rol"] = user["rol"]
            session["inventario_id"] = user["inventario_id"]
            session["email"] = user["email"]
            session["nombre"] = user.get("nombre", user["email"])

            if request.is_json:
                # ✅ Enviar respuesta JSON con ok=true
                return jsonify({"ok": True, "redirect": "/admin" if user["rol"] == "admin" else "/index"})
            else:
                return redirect("/admin" if user["rol"] == "admin" else "/index")

        # ✅ Login fallido - enviar mensaje de error
        if request.is_json:
            return jsonify({"ok": False, "msg": mensaje_error})
        else:
            flash(mensaje_error)
            return redirect("/login")

    return render_template("login.html")


# ================= REGISTER (CORREGIDO - ENVÍA MENSAJES) =================
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

        # Validar que no estén vacíos
        if not email or not password:
            if request.is_json:
                return jsonify({"ok": False, "msg": "Correo y contraseña son requeridos"})
            else:
                flash("Correo y contraseña son requeridos")
                return redirect("/register")

        conn = get_db()
        cur = conn.cursor()

        # Verificar si el usuario ya existe
        cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        if cur.fetchone():
            conn.close()
            if request.is_json:
                return jsonify({"ok": False, "msg": "El correo ya está registrado"})
            else:
                flash("El correo ya está registrado")
                return redirect("/register")

        # Crear inventario para el nuevo usuario
        nombre_inventario = f"Inventario de {email}"
        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (nombre_inventario,))
        inventario_id = cur.lastrowid

        # Crear usuario (contraseña en texto plano)
        nombre_usuario = email.split('@')[0] if '@' in email else email
        cur.execute("""
        INSERT INTO usuarios (email, password, rol, inventario_id, nombre)
        VALUES (?, ?, 'usuario', ?, ?)
        """, (email, password, inventario_id, nombre_usuario))

        conn.commit()
        conn.close()

        # ✅ Registro exitoso
        if request.is_json:
            return jsonify({"ok": True, "msg": "Usuario creado exitosamente"})
        else:
            flash("Usuario registrado exitosamente")
            return redirect("/login")

    return render_template("register.html")


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


# ================= BUSCAR =================
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

    categoria_select = request.form.get("categoria_select", "")
    nueva_categoria = request.form.get("nueva_categoria", "")
    
    if categoria_select == "nueva":
        categoria = nueva_categoria
    else:
        categoria = categoria_select

    if not categoria:
        flash("❌ Categoría inválida")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO productos (nombre, categoria, precio, cantidad, inventario_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.form["nombre"],
        categoria,
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

    cur.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id=?", (cantidad, id))
    cur.execute("""
        INSERT INTO ventas (producto_id, producto, cantidad, precio, fecha, inventario_id) 
        VALUES (?, ?, ?, ?, datetime('now'), ?)
    """, (id, producto["nombre"], cantidad, producto["precio"], session["inventario_id"]))

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

    cur.execute("SELECT id, nombre, cantidad, precio FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()

    cur.execute("""
        SELECT v.id, v.producto, v.cantidad, v.precio, v.fecha
        FROM ventas v
        WHERE v.inventario_id=?
        ORDER BY v.id DESC
        LIMIT 50
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
    cur.execute("""
        INSERT INTO ventas (producto_id, producto, cantidad, precio, fecha, inventario_id) 
        VALUES (?, ?, ?, ?, datetime('now'), ?)
    """, (producto_id, producto["nombre"], cantidad, producto["precio"], session["inventario_id"]))

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
    SELECT SUM(cantidad * precio) as ventas
    FROM ventas
    WHERE inventario_id=?
    """, (session["inventario_id"],))
    ventas_total = cur.fetchone()["ventas"] or 0

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

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT nombre, categoria, cantidad, precio
    FROM productos
    WHERE inventario_id=?
    """, (session["inventario_id"],))

    data = [["Nombre", "Categoría", "Cantidad", "Precio"]]

    for row in cur.fetchall():
        data.append([row["nombre"], row["categoria"], row["cantidad"], f"${row['precio']:,.2f}"])

    conn.close()

    table = Table(data)
    doc.build([table])

    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="reporte.pdf", mimetype='application/pdf')


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= MAIN =================
if __name__ == "__main__":
    init_db()
    
    print("\n" + "="*50)
    print("🚀 APLICACIÓN INICIADA")
    print("="*50)
    print("📁 Base de datos:", "/tmp/inventario.db" if os.environ.get("RENDER") else "inventario.db")
    print("🔐 CREDENCIALES DE PRUEBA:")
    print("   admin@email.com / admin123")
    print("   repmotos@email.com / 123456")
    print("   test@email.com / (cualquier contraseña)")
    print("="*50 + "\n")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
