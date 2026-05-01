📦 Sistema Web de Gestión de Inventarios
🧾 Descripción

Aplicación web desarrollada en Python con Flask que permite la gestión de inventarios en un entorno multiusuario.
Cada usuario administra su propio inventario, mientras que el administrador controla usuarios e inventarios.

El sistema incluye funcionalidades de productos, ventas, dashboard y reportes en PDF.

🎯 Objetivo

Desarrollar un sistema que permita:

Controlar inventarios por usuario
Registrar ventas y actualizar stock automáticamente
Visualizar métricas clave en un dashboard
Generar reportes descargables
Administrar usuarios e inventarios
⚙️ Tecnologías Utilizadas
Backend: Python + Flask
Base de datos: SQLite
Frontend: HTML, CSS, JavaScript
Librerías adicionales:
Axios (peticiones HTTP)
ReportLab (generación de PDF)
👥 Roles del Sistema
🔐 Administrador
Crear usuarios
Crear inventarios
Asignar inventarios a usuarios
Visualizar todos los datos del sistema
👤 Usuario
Gestionar productos
Registrar ventas
Consultar dashboard
Descargar reportes PDF
Ver historial de ventas
🚀 Funcionalidades
📦 Gestión de Inventario
Agregar productos
Eliminar productos
Actualizar cantidades (sumar stock)
Manejo de categorías dinámas
💰 Ventas
Registro de ventas
Reducción automática del stock
Control de stock insuficiente
Historial de ventas por usuario
📊 Dashboard
Total de productos
Stock disponible (suma real del inventario)
Ventas filtradas por inventario
Top productos más vendidos
📄 Reportes
Generación de reportes en PDF
Descarga directa desde el dashboard
⚙️ Administración
Creación de usuarios
Creación de inventarios
Asignación de inventarios a usuarios
🗂️ Estructura del Proyecto
inventario/
│
├── app.py
├── crear_db.py
├── inventario.db
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   ├── dashboard.html
│   ├── ventas.html
│   └── admin.html
│
├── static/
│   ├── style.css
│   └── logo.png
🛠️ Instalación
1️⃣ Clonar el proyecto
git clone <repositorio>
cd inventario
2️⃣ Instalar dependencias
pip install flask reportlab
3️⃣ Crear base de datos
python crear_db.py
4️⃣ Ejecutar la aplicación
python app.py
5️⃣ Acceder al sistema
http://127.0.0.1:3000
🔑 Usuarios de Prueba
Rol	Usuario	Contraseña
Admin	admin@email.com
	admin123
Usuario	repmotos@email.com
	123456
🧪 Pruebas Realizadas
✔ Login y autenticación
✔ Registro de usuarios
✔ CRUD de productos
✔ Registro de ventas
✔ Validación de stock
✔ Dashboard (métricas correctas)
✔ Generación de PDF
✔ Control de roles
✔ Aislamiento de datos por inventario
📊 Resultados
✔ Sistema funcional y estable
✔ Separación correcta de datos por usuario
✔ Métricas reales en dashboard
✔ Flujo completo de inventario y ventas
✔ Reportes descargables
⚠️ Problemas y Soluciones
Problema	Solución
Error login (KeyError)	Soporte JSON + form
Tabla ventas inexistente	Creación automática
Ventas mal calculadas	Se filtró por inventario
Dashboard incorrecto	Ajuste de consultas SQL
PDF no descargaba	Implementación con ReportLab
🔐 Seguridad
Manejo de sesiones con Flask
Restricción de rutas por rol
Validación de duplicados
Aislamiento de información por inventario
📈 Mejoras Futuras
📊 Gráficas dinámicas en dashboard
📄 Exportación avanzada de reportes
🔔 Alertas de bajo stock
🔐 Encriptación de contraseñas
🌐 API REST
📚 Conclusión

El sistema cumple con los requerimientos funcionales planteados, permitiendo una gestión eficiente del inventario en un entorno multiusuario.
Se garantiza la integridad de los datos mediante separación por inventarios y control de acceso.

👨‍💻 Autor

Juan Arévalo
Proyecto académico – Desarrollo de Aplicaciones Web