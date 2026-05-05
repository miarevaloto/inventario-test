from flask import Flask, render_template, request, redirect, session, flash
from reportlab.platypus import SimpleDocTemplate, Table
from flask import send_file
import io
import sqlite3
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

    # 🔥 evitar que admin entre aquí
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

    nombre = request.form["nombre"]
    categoria = request.form["categoria"]

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
    """, (nombre, categoria, precio, cantidad, session["inventario_id"]))

    conn.commit()
    conn.close()

    flash("✅ Producto agregado")
    return redirect("/index")


# ================= SUMAR =================
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


# ================= VENDER =================
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


# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))

    conn.commit()
    conn.close()

    return redirect("/index")


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

    conn.close()

    return render_template("dashboard.html",
        total_productos=total_productos,
        stock_total=stock_total,
        ventas_total=ventas_total
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


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= MAIN =================
if __name__ == "__main__":
    init_db()  # 🔥 importante
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
