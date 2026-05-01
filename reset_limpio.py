import sqlite3

conn = sqlite3.connect("inventario.db")
cur = conn.cursor()

# =========================
# CREAR TABLAS LIMPIAS
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS inventarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    rol TEXT,
    inventario_id INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS productos_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    categoria TEXT,
    cantidad INTEGER,
    precio REAL,
    iva REAL,
    vendidos INTEGER,
    inventario_id INTEGER
)
""")

# =========================
# CREAR INVENTARIO REPMOTOS
# =========================

cur.execute("SELECT id FROM inventarios WHERE nombre='repmotos'")
inv = cur.fetchone()

if not inv:
    cur.execute("INSERT INTO inventarios (nombre) VALUES ('repmotos')")
    inventario_id = cur.lastrowid
else:
    inventario_id = inv[0]

# =========================
# MIGRAR USUARIOS
# =========================

cur.execute("SELECT id, email, password, rol FROM usuarios")
usuarios = cur.fetchall()

for u in usuarios:
    cur.execute("""
    INSERT INTO usuarios_new (id, email, password, rol, inventario_id)
    VALUES (?, ?, ?, ?, ?)
    """, (u[0], u[1], u[2], u[3], inventario_id))

# =========================
# MIGRAR PRODUCTOS
# =========================

cur.execute("SELECT * FROM productos")
productos = cur.fetchall()

for p in productos:
    cur.execute("""
    INSERT INTO productos_new (id, nombre, categoria, cantidad, precio, iva, vendidos, inventario_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (p[0], p[1], p[2], p[3], p[4], p[5], p[6], inventario_id))

# =========================
# REEMPLAZAR TABLAS
# =========================

cur.execute("DROP TABLE usuarios")
cur.execute("DROP TABLE productos")

cur.execute("ALTER TABLE usuarios_new RENAME TO usuarios")
cur.execute("ALTER TABLE productos_new RENAME TO productos")

conn.commit()
conn.close()

print("✅ BD LIMPIA Y NORMALIZADA SIN PERDER DATOS")