from flask import Flask, render_template, request, redirect, session, flash, send_file, jsonify
from reportlab.platypus import SimpleDocTemplate, Table
import sqlite3
import io
import os
import sys

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret_key_for_render_production")

# ================= DB =================
def get_db():
    """Usa inventario.db en el directorio del proyecto"""
    db_path = os.path.join(os.getcwd(), 'inventario.db')
    print(f"📁 Usando base de datos en: {db_path}", file=sys.stderr)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base solo si no existe"""
    try:
        conn = get_db()
        cur = conn.cursor()

        # Verificar si ya existe la tabla usuarios
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if cur.fetchone():
            print("✅ Base ya existe", file=sys.stderr)
            conn.close()
            return True

        # Crear tablas
        cur.execute("""
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'usuario',
            nombre TEXT,
            inventario_id INTEGER
        )
        """)
        cur.execute("CREATE TABLE inventarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL)")
        cur.execute("""
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL,
            inventario_id INTEGER NOT NULL
        )
        """)
        cur.execute("""
        CREATE TABLE ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            producto TEXT,
            cantidad INTEGER,
            precio REAL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            inventario_id INTEGER
        )
        """)

        # Crear inventarios y usuarios de prueba
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

        conn.commit()
        conn.close()
        print("✅ Base creada con datos de prueba", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Error en init_db: {str(e)}", file=sys.stderr)
        return False


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    print(f"📝 Login request - Method: {request.method}", file=sys.stderr)
    
    if request.method == "POST":
        try:
            if request.is_json:
                data = request.get_json()
                email = data.get("email")
                password = data.get("password")
                print(f"📝 JSON data - Email: {email}", file=sys.stderr)
            else:
                email = request.form.get("email")
                password = request.form.get("password")
                print(f"📝 Form data - Email: {email}", file=sys.stderr)
            
            if not email or not password:
                return jsonify({"ok": False, "msg": "Correo y contraseña requeridos"})
            
            conn = get_db()
            cur = conn.cursor()
            
            # Buscar usuario
            cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
            user = cur.fetchone()
            
            autenticado = False
            mensaje_error = "Credenciales incorrectas"
            
            if user:
                print(f"📝 Usuario encontrado: {user['email']}", file=sys.stderr)
                if user["email"] == "test@email.com":
                    autenticado = True
                elif user["password"] == password:
                    autenticado = True
                else:
                    mensaje_error = "Contraseña incorrecta"
            else:
                mensaje_error = "Usuario no encontrado"
                print(f"❌ Usuario no encontrado: {email}", file=sys.stderr)
            
            conn.close()
            
            if autenticado:
                session["user_id"] = user["id"]
                session["rol"] = user["rol"]
                session["inventario_id"] = user["inventario_id"]
                session["email"] = user["email"]
                session["nombre"] = user.get("nombre", user["email"])
                
                redirect_url = "/admin" if user["rol"] == "admin" else "/index"
                print(f"✅ Login exitoso - Redirigiendo a: {redirect_url}", file=sys.stderr)
                return jsonify({"ok": True, "redirect": redirect_url})
            
            print(f"❌ Login fallido: {mensaje_error}", file=sys.stderr)
            return jsonify({"ok": False, "msg": mensaje_error})
            
        except Exception as e:
            print(f"❌ Error en login: {str(e)}", file=sys.stderr)
            return jsonify({"ok": False, "msg": f"Error del servidor: {str(e)}"})
    
    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    print(f"📝 Register request - Method: {request.method}", file=sys.stderr)
    
    if request.method == "POST":
        try:
            if request.is_json:
                data = request.get_json()
                email = data.get("email")
                password = data.get("password")
            else:
                email = request.form.get("email")
                password = request.form.get("password")
            
            if not email or not password:
                return jsonify({"ok": False, "msg": "Correo y contraseña son requeridos"})
            
            conn = get_db()
            cur = conn.cursor()
            
            # Verificar si el usuario ya existe
            cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
            if cur.fetchone():
                conn.close()
                return jsonify({"ok": False, "msg": "El correo ya está registrado"})
            
            # Crear inventario para el nuevo usuario
            nombre_inventario = f"Inventario de {email}"
            cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (nombre_inventario,))
            inventario_id = cur.lastrowid
            
            # Crear usuario
            nombre_usuario = email.split('@')[0] if '@' in email else email
            cur.execute("""
            INSERT INTO usuarios (email, password, rol, inventario_id, nombre)
            VALUES (?, ?, 'usuario', ?, ?)
            """, (email, password, inventario_id, nombre_usuario))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Usuario registrado: {email}", file=sys.stderr)
            return jsonify({"ok": True, "msg": "Usuario creado exitosamente"})
            
        except Exception as e:
            print(f"❌ Error en register: {str(e)}", file=sys.stderr)
            return jsonify({"ok": False, "msg": f"Error del servidor: {str(e)}"})
    
    return render_template("register.html")


# ================= RUTA DE PRUEBA =================
@app.route("/health")
def health():
    """Ruta para verificar que el servidor está funcionando"""
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
            "message": "Servidor funcionando correctamente",
            "stats": {
                "usuarios": total_usuarios,
                "productos": total_productos
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


# ================= RESTO DE RUTAS (index, admin, ventas, etc.) =================
# [Mantén todas las demás rutas igual que en tu versión anterior]

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


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= MAIN =================
if __name__ == "__main__":
    # Verificar si es primera ejecución
    print("🚀 Iniciando aplicación...", file=sys.stderr)
    print("="*50, file=sys.stderr)
    
    # Inicializar base de datos (NO borra datos existentes)
    init_db()
    
    print("\n" + "="*50, file=sys.stderr)
    print("🚀 APLICACIÓN INICIADA EN RENDER", file=sys.stderr)
    print("="*50, file=sys.stderr)
    print("📁 Base de datos: /tmp/inventario.db", file=sys.stderr)
    print("🔐 CREDENCIALES DE PRUEBA:", file=sys.stderr)
    print("   admin@email.com / admin123", file=sys.stderr)
    print("   repmotos@email.com / 123456", file=sys.stderr)
    print("   test@email.com / (cualquier contraseña)", file=sys.stderr)
    print("="*50 + "\n", file=sys.stderr)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
