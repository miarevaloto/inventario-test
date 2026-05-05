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

            redirect_url = "/admin" if user["rol"] == "admin" else "/index"
            return redirect(redirect_url)

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


# ================= AGREGAR =================
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    categoria = request.form.get("categoria_select")
    nueva = request.form.get("nueva_categoria")

    if categoria == "nueva":
        categoria_final = nueva
    else:
        categoria_final = categoria

    try:
        cantidad = int(request.form["cantidad"])
        precio = float(request.form["precio"])
    except:
        flash("❌ Datos inválidos")
        return redirect("/index")

    if cantidad <= 0 or precio <= 0:
        flash("❌ Valores inválidos")
        return redirect("/index")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO productos (nombre,categoria,cantidad,precio,iva,vendidos,inventario_id)
    VALUES (?,?,?,?,0.19,0,?)
    """, (
        request.form["nombre"],
        categoria_final,
        cantidad,
        precio,
        session["inventario_id"]
    ))

    conn.commit()
    conn.close()

    flash("✅ Producto agregado")
    return redirect("/index")


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

    cur.execute("""
        SELECT * FROM productos
        WHERE id=? AND inventario_id=?
    """, (producto_id, session["inventario_id"]))
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

    return render_template("index.html",
        productos=productos,
        categorias=categorias,
        producto_buscado=producto
    )


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

    cur.execute("""
        SELECT * FROM productos
        WHERE id=? AND inventario_id=?
    """, (id, session["inventario_id"]))
    producto = cur.fetchone()

    if not producto:
        conn.close()
        flash("❌ Producto no válido")
        return redirect("/index")

    if cantidad > producto["cantidad"]:
        conn.close()
        flash("❌ Stock insuficiente")
        return redirect("/index")

    nueva_cantidad = producto["cantidad"] - cantidad

    cur.execute("UPDATE productos SET cantidad=? WHERE id=?", (nueva_cantidad, id))

    cur.execute("""
        INSERT INTO ventas (producto_id, cantidad)
        VALUES (?, ?)
    """, (id, cantidad))

    conn.commit()
    conn.close()

    flash("✅ Venta realizada")
    return redirect("/index")


# ================= ELIMINAR =================
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM productos WHERE id=? AND inventario_id=?", (id, session["inventario_id"]))

    conn.commit()
    conn.close()

    flash("🗑️ Producto eliminado")
    return redirect("/index")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= MAIN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True)
