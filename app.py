from flask import Flask, render_template, request, redirect, session, flash, send_file
from reportlab.platypus import SimpleDocTemplate, Table
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

            return redirect("/admin" if user["rol"] == "admin" else "/index")

        flash("❌ Credenciales incorrectas")

    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        if cur.fetchone():
            conn.close()
            flash("❌ Usuario ya existe")
            return redirect("/register")

        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (f"Inventario de {email}",))
        inventario_id = cur.lastrowid

        cur.execute("""
        INSERT INTO usuarios (email,password,rol,inventario_id)
        VALUES (?,?, 'usuario',?)
        """,(email,password,inventario_id))

        conn.commit()
        conn.close()

        flash("✅ Usuario registrado")
        return redirect("/login")

    return render_template("register.html")


# ================= INDEX =================
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


# ================= DASHBOARD (RESTAURADO) =================
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


# ================= VENTAS (RESTAURADO) =================
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
    """, (session["inventario_id"],))
    ventas = cur.fetchall()

    conn.close()

    return render_template("ventas.html", productos=productos, ventas=ventas)


# ================= ADD (CORREGIDO) =================
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    categoria = request.form.get("categoria_select")
    nueva = request.form.get("nueva_categoria")

    categoria_final = nueva if categoria == "nueva" else categoria

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO productos (nombre,categoria,cantidad,precio,iva,vendidos,inventario_id)
    VALUES (?,?,?,?,0.19,0,?)
    """, (
        request.form["nombre"],
        categoria_final,
        request.form["cantidad"],
        request.form["precio"],
        session["inventario_id"]
    ))

    conn.commit()
    conn.close()

    flash("✅ Producto agregado")
    return redirect("/index")


# ================= SUMAR (CORREGIDO) =================
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

    cantidad = int(request.form["cantidad"])

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))
    producto = cur.fetchone()

    if cantidad > producto["cantidad"]:
        flash("❌ Stock insuficiente")
        conn.close()
        return redirect("/index")

    nueva_cantidad = producto["cantidad"] - cantidad

    cur.execute("UPDATE productos SET cantidad=? WHERE id=?", (nueva_cantidad, id))
    cur.execute("INSERT INTO ventas (producto_id, cantidad) VALUES (?, ?)", (id, cantidad))

    conn.commit()
    conn.close()

    flash("✅ Venta realizada")
    return redirect("/index")


# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))

    conn.commit()
    conn.close()

    return redirect("/index")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= MAIN =================
if __name__ == "__main__":
    app.run(debug=True)
