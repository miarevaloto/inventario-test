# 📦 Sistema de Gestión de Inventario

Aplicación web desarrollada con **Flask** para la gestión de inventarios, ventas y usuarios, con control de acceso por roles (usuario y administrador).

---

## 🚀 🌐 Aplicación en Producción

🔗 https://inventario-test.onrender.com/login

---

## 🧠 Descripción del Proyecto

Este sistema permite a los usuarios:

* Gestionar productos (crear, editar, eliminar)
* Controlar el inventario
* Registrar ventas
* Visualizar métricas en dashboard
* Administrar usuarios (rol administrador)
* Trabajar con datos aislados por inventario

---

## 🛠️ Tecnologías Utilizadas

* Python 3
* Flask
* SQLite
* HTML5 / CSS3
* Jinja2
* Gunicorn (producción)
* Render (deploy)

---

## 📂 Estructura del Proyecto

```
inventario-test/
│
├── app.py
├── database.db
├── requirements.txt
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   ├── ventas.html
│   ├── dashboard.html
│   └── admin.html
│
├── static/
│   └── style.css
```

---

## ⚙️ Instalación Local

1. Clonar repositorio:

```bash
git clone https://github.com/miarevaloto/inventario-test.git
cd inventario-test
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar:

```bash
python app.py
```

4. Abrir en navegador:

```
http://127.0.0.1:5000/login
```

---

## 🔐 Funcionalidades Principales

### 👤 Autenticación

* Login de usuario
* Registro de usuario
* Control de sesión

---

### 📦 Inventario

* Agregar productos
* Editar productos
* Eliminar productos
* Buscar producto por ID
* Validación de datos (precio y cantidad)

---

### 💰 Ventas

* Registrar ventas
* Validar stock disponible
* Evitar ventas inválidas
* Historial de ventas

---

### 📊 Dashboard

* Total de productos
* Stock disponible
* Ventas totales
* Top productos más vendidos

---

### 🛠️ Administración

* Crear usuarios
* Eliminar usuarios
* Asignar inventarios

---

## 🔒 Validaciones Implementadas

✔ No se permiten valores negativos en:

* Cantidad de productos
* Precio de productos
* Ventas

✔ Validaciones en:

* Frontend (HTML + JavaScript)
* Backend (Flask)

✔ Mensajes de error y éxito mediante `flash()`

---

## 🧪 Pruebas de Software

* Total de casos de prueba: 23
* Casos ejecutados: 23
* Casos exitosos: 22
* Casos fallidos: 1

### 📊 Métricas

* Cobertura: 100%
* Tasa de éxito: 95.6%
* Defectos: 4.3%

---

## 🐞 Defectos Detectados

* Validación incompleta en registro de usuarios (campos vacíos)

---

## 📈 Estado del Proyecto

✔ Sistema funcional
✔ Desplegado en producción
✔ Validado mediante pruebas
✔ Pendiente mejora menor en registro

---

## 🚀 Deploy

La aplicación está desplegada en:

**Render**

Configuración:

```
Build: pip install -r requirements.txt
Start: gunicorn app:app
```

---

## 📌 Recomendaciones Futuras

* Migrar base de datos a PostgreSQL
* Implementar autenticación segura (hash de contraseñas)
* Mejorar UI/UX
* Implementar API REST
* Agregar pruebas automáticas

---

## 👨‍💻 Autor

Proyecto desarrollado para la asignatura **Pruebas de Software**

---

## 📄 Licencia

Uso académico
