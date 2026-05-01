import sqlite3

conn = sqlite3.connect("inventario.db")
cur = conn.cursor()

# =========================
# TABLAS
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS inventarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    rol TEXT,
    inventario_id INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS productos (
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
# INVENTARIO BASE
# =========================

cur.execute("INSERT INTO inventarios (nombre) VALUES ('repmotos')")
inventario_id = cur.lastrowid

# =========================
# USUARIOS
# =========================

cur.execute("""
INSERT INTO usuarios (email, password, rol, inventario_id)
VALUES ('admin@email.com', 'admin123', 'admin', ?)
""", (inventario_id,))

cur.execute("""
INSERT INTO usuarios (email, password, rol, inventario_id)
VALUES ('repmotos@email.com', '123456', 'usuario', ?)
""", (inventario_id,))

# =========================
# PRODUCTOS (10 ITEMS)
# =========================

productos = [
    ("Aceite 4T", "Lubricantes", 20, 25000, 0.19, 0),
    ("Filtro de aire", "Repuestos", 30, 15000, 0.19, 0),
    ("Bujía NGK", "Repuestos", 40, 10000, 0.19, 0),
    ("Casco integral", "Accesorios", 15, 120000, 0.19, 0),
    ("Guantes moto", "Accesorios", 25, 30000, 0.19, 0),
    ("Cadena moto", "Transmisión", 20, 80000, 0.19, 0),
    ("Kit arrastre", "Transmisión", 10, 150000, 0.19, 0),
    ("Llanta delantera", "Llantas", 18, 90000, 0.19, 0),
    ("Llanta trasera", "Llantas", 15, 110000, 0.19, 0),
    ("Pastillas de freno", "Frenos", 35, 20000, 0.19, 0)
]

for p in productos:
    cur.execute("""
    INSERT INTO productos 
    (nombre, categoria, cantidad, precio, iva, vendidos, inventario_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (*p, inventario_id))

conn.commit()
conn.close()

print("✅ Base de datos creada")