from flask import Flask, render_template, request, redirect, session, flash
from reportlab.platypus import SimpleDocTemplate, Table
from flask import send_file
import io
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"


# ================= DB =================
def get_db():
    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # tabla ventas si no existe
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER,
        cantidad INTEGER
    )
    """)

    conn.commit()
    conn.close()


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

            redirect_url = "/admin" if user["rol"] == "admin" else "/index"

            return {"ok": True, "redirect": redirect_url} if request.is_json else redirect(redirect_url)

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

        # crear inventario automático
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


# ================= INVENTARIO =================
@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()

    cur.execute("SELECT DISTINCT categoria FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    categorias = cur.fetchall()

    conn.close()

    return render_template("index.html", productos=productos, categorias=categorias)

@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():
    if "user_id" not in session:
        return redirect("/login")

    nombre = request.form["nombre"]
    categoria = request.form["categoria"]

    try:
        precio = float(request.form["precio"])
    except:
        flash("❌ Precio inválido")
        return redirect("/index")

    try:
        cantidad = int(request.form["cantidad"])
    except:
        flash("❌ Cantidad inválida")
        return redirect("/index")

    # 🔴 VALIDACIONES
    if precio < 1:
        flash("❌ El precio no puede ser negativo")
        return redirect("/index")

    if cantidad < 1:
        flash("❌ La cantidad no puede ser negativa")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO productos (nombre, categoria, precio, cantidad, inventario_id)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, categoria, precio, cantidad, session["inventario_id"]))

    conn.commit()
    conn.close()

    flash("✅ Producto agregado correctamente")
    return redirect("/index")

@app.route("/buscar_producto", methods=["POST"])
def buscar_producto():
    if "user_id" not in session:
        return redirect("/login")

    try:
        producto_id = int(request.form["id"])
    except:
        flash("❌ ID inválido")
        return redirect("/index")

    if producto_id <= 0:
        flash("❌ ID inválido")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM productos
        WHERE id=? AND inventario_id=?
    """, (producto_id, session["inventario_id"]))
    producto = cur.fetchone()

    conn.close()

    if not producto:
        flash("❌ Producto no encontrado")
        return redirect("/index")

    # 🔥 IMPORTANTE: volver a cargar todo el index
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE inventario_id=?", (session["inventario_id"],))
    productos = cur.fetchall()

    conn.close()

    return render_template("index.html", productos=productos, producto_buscado=producto)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # TOTAL PRODUCTOS
    cur.execute("""
    SELECT COUNT(*) as total 
    FROM productos 
    WHERE inventario_id=?
    """, (session["inventario_id"],))
    total_productos = cur.fetchone()["total"]

    # STOCK TOTAL
    cur.execute("""
    SELECT SUM(cantidad) as stock 
    FROM productos 
    WHERE inventario_id=?
    """, (session["inventario_id"],))
    stock_total = cur.fetchone()["stock"] or 0

    # VENTAS TOTALES
    cur.execute("""
    SELECT SUM(v.cantidad * p.precio) as ventas
    FROM ventas v
    JOIN productos p ON v.producto_id = p.id
    WHERE p.inventario_id=?
    """, (session["inventario_id"],))
    ventas_total = cur.fetchone()["ventas"] or 0

    # 🔥 TOP PRODUCTOS CORRECTO
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

# ================= PAGINA VENTAS =================
@app.route("/ventas")
def ventas():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Productos del usuario
    cur.execute("""
        SELECT * FROM productos
        WHERE inventario_id=?
    """, (session["inventario_id"],))
    productos = cur.fetchall()

    # Historial de ventas
    cur.execute("""
        SELECT v.id, p.nombre as producto, v.cantidad
        FROM ventas v
        JOIN productos p ON v.producto_id = p.id
        WHERE p.inventario_id=?
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
        flash("❌ Venta inválida: datos incorrectos")
        return redirect("/ventas")

    if cantidad <= 1:
        flash("❌ Venta inválida: cantidad debe ser mayor a 1")
        return redirect("/ventas")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM productos
        WHERE id=? AND inventario_id=?
    """, (producto_id, session["inventario_id"]))
    producto = cur.fetchone()

    if not producto:
        flash("❌ Producto no válido")
        conn.close()
        return redirect("/ventas")

    if cantidad > producto["cantidad"]:
        flash("❌ Stock insuficiente")
        conn.close()
        return redirect("/ventas")

    nueva_cantidad = producto["cantidad"] - cantidad

    cur.execute("""
        UPDATE productos SET cantidad=?
        WHERE id=?
    """, (nueva_cantidad, producto_id))

    cur.execute("""
        INSERT INTO ventas (producto_id, cantidad)
        VALUES (?, ?)
    """, (producto_id, cantidad))

    conn.commit()
    conn.close()

    flash("✅ Venta realizada correctamente")
    return redirect("/ventas")

# ================= AGREGAR =================
@app.route("/add", methods=["POST"])
def add():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO productos (nombre,categoria,cantidad,precio,iva,vendidos,inventario_id)
    VALUES (?,?,?,?,0.19,0,?)
    """, (
        request.form["nombre"],
        request.form["categoria"],
        request.form["cantidad"],
        request.form["precio"],
        session["inventario_id"]
    ))

    conn.commit()
    conn.close()

    return redirect("/index")


# ================= SUMAR =================
@app.route("/sumar/<int:id>", methods=["POST"])
def sumar(id):
    cantidad = int(request.form["cantidad"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE productos
    SET cantidad = cantidad + ?
    WHERE id=? AND inventario_id=?
    """, (cantidad, id, session["inventario_id"]))

    cantidad = int(request.form["cantidad"])

    # ❌ SIN VALIDACIÓN (error intencional)
    nueva_cantidad = producto["cantidad"] + cantidad

    conn.commit()
    conn.close()

    return redirect("/index")


# ================= VENDER =================
@app.route("/vender/<int:id>", methods=["POST"])
def vender(id):
    if "user_id" not in session:
        return redirect("/login")

    try:
        cantidad = int(request.form["cantidad"])
    except:
        flash("❌ Venta inválida: datos incorrectos")
        return redirect("/index")

    # 🔴 VALIDACIÓN CLAVE
    if cantidad <= 0:
        flash("❌ Venta inválida: la cantidad debe ser mayor a 0")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    # Obtener producto
    cur.execute("""
        SELECT * FROM productos
        WHERE id=? AND inventario_id=?
    """, (id, session["inventario_id"]))
    producto = cur.fetchone()

    if not producto:
        flash("❌ Producto no válido")
        conn.close()
        return redirect("/index")

    # 🔴 STOCK INSUFICIENTE
    if cantidad > producto["cantidad"]:
        flash("❌ Stock insuficiente")
        conn.close()
        return redirect("/index")

    # ✅ ACTUALIZAR STOCK
    nueva_cantidad = producto["cantidad"] - cantidad

    cur.execute("""
        UPDATE productos SET cantidad=?
        WHERE id=?
    """, (nueva_cantidad, id))

    # ✅ REGISTRAR VENTA
    cur.execute("""
        INSERT INTO ventas (producto_id, cantidad)
        VALUES (?, ?)
    """, (id, cantidad))

    conn.commit()
    conn.close()

    flash("✅ Venta realizada correctamente")
    return redirect("/index")

# ================= ELIMINAR =================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))

    conn.commit()
    conn.close()

    return redirect("/index")


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

# ================= ELIMINAR USUARIO + INVENTARIO =================
@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if "user_id" not in session or session.get("rol") != "admin":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Evitar eliminarse a sí mismo
    if id == session["user_id"]:
        conn.close()
        return "No puedes eliminar tu propio usuario"

    # 1. Obtener inventario del usuario
    cur.execute("SELECT inventario_id FROM usuarios WHERE id=?", (id,))
    user = cur.fetchone()

    if user and user["inventario_id"]:
        inventario_id = user["inventario_id"]

        # 2. Eliminar productos de ese inventario
        cur.execute("DELETE FROM productos WHERE inventario_id=?", (inventario_id,))

        # 3. Eliminar inventario
        cur.execute("DELETE FROM inventarios WHERE id=?", (inventario_id,))

    # 4. Eliminar usuario
    cur.execute("DELETE FROM usuarios WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= REPORTE =================
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
        data.append([row["nombre"], row["categoria"], row["cantidad"], row["precio"]])

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
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)