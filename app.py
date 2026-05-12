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
        cur.execute("SELECT * FROM usuarios WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["rol"] = user["rol"]
            session["inventario_id"] = user["inventario_id"]
            # Si tienes columna nombre, úsala. Si no, usa el email.
            session["nombre"] = user["nombre"] if "nombre" in user.keys() else user["email"]

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
            nombre = data.get("nombre", email)  # si no envías nombre, usa email
        else:
            email = request.form.get("email")
            password = request.form.get("password")
            nombre = request.form.get("nombre", email)

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        if cur.fetchone():
            conn.close()
            return {"ok": False, "msg": "Usuario ya existe"}

        cur.execute("INSERT INTO inventarios (nombre) VALUES (?)", (f"Inventario de {email}",))
        inventario_id = cur.lastrowid

        cur.execute("""
        INSERT INTO usuarios (nombre, email, password, rol, inventario_id)
        VALUES (?, ?, ?, 'usuario', ?)
        """, (nombre, email, password, inventario_id))

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

    return render_template("index.html",
                           productos=productos,
                           categorias=categorias,
                           nombre=session.get("nombre"))

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

    return render_template("index.html",
                           productos=productos,
                           categorias=categorias,
                           producto_buscado=producto,
                           nombre=session.get("nombre"))

# (el resto de rutas: agregar_producto, sumar, vender, delete, ventas, dashboard, admin, crear_usuario_admin, modificar_inventario, eliminar_inventario, reporte_pdf, logout se mantienen igual que ya tienes, solo asegúrate de que en crear_usuario_admin también insertes el campo nombre en la tabla usuarios)

# ================= MAIN =================
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
