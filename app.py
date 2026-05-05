from flask import Flask, render_template, request, redirect, session, flash, send_file
from reportlab.platypus import SimpleDocTemplate, Table
import sqlite3
import io
import os

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

    conn.close()

    return render_template("index.html", productos=productos, categorias=categorias)


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

    conn.close()

    return render_template("index.html", productos=productos, categorias=categorias, producto_buscado=producto)


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

    cur.execute("SELECT inventario_id FROM usuarios WHERE id=?", (id,))
    user = cur.fetchone()

    if user:
        cur.execute("DELETE FROM productos WHERE inventario_id=?", (user["inventario_id"],))
        cur.execute("DELETE FROM inventarios WHERE id=?", (user["inventario_id"],))

    cur.execute("DELETE FROM usuarios WHERE id=?", (id,))

    conn.commit()
    conn.close()

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
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
