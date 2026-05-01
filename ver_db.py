import sqlite3

conn = sqlite3.connect("inventario.db")
cur = conn.cursor()

print("\n=== USUARIOS ===")
for row in cur.execute("SELECT * FROM usuarios"):
    print(row)

print("\n=== PRODUCTOS ===")
for row in cur.execute("SELECT * FROM productos"):
    print(row)

print("\n=== INVENTARIOS ===")
for row in cur.execute("SELECT * FROM inventarios"):
    print(row)

conn.close()