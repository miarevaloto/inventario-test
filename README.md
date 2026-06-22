# 🏍️ Sistema de Gestión de Inventario para Talleres de Motos

![Django](https://img.shields.io/badge/Django-4.2.7-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Render](https://img.shields.io/badge/Render-Deploy-46E3B7?style=for-the-badge&logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-FF6B6B?style=for-the-badge)

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Local](#-instalación-local)
- [Despliegue en Render](#-despliegue-en-render)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Base de Datos](#-base-de-datos)
- [API Endpoints](#-api-endpoints)
- [Variables de Entorno](#-variables-de-entorno)
- [Credenciales de Prueba](#-credenciales-de-prueba)
- [Contribución](#-contribución)
- [Licencia](#-licencia)
- [Contacto](#-contacto)

---

## 📖 Descripción

**Sistema de Gestión de Inventario** diseñado específicamente para talleres y tiendas de repuestos de motos. Permite administrar múltiples tiendas, cada una con su propio inventario independiente, gestionar productos, ventas, generar reportes y obtener análisis en tiempo real.

### 🎯 **Propósito del Proyecto**

Este proyecto fue desarrollado como **trabajo de grado** para la carrera de **Ingeniería de Sistemas**, demostrando la aplicación de tecnologías modernas en la resolución de problemas empresariales reales.

**Ideal para:**
- ✅ Talleres de mantenimiento de motos
- ✅ Tiendas de repuestos y accesorios
- ✅ Distribuidores de productos para motos
- ✅ Pequeñas y medianas empresas del sector automotriz

---

## ✨ Características

### 🏢 **Multi-Tienda**
- Gestión de **múltiples tiendas** con inventarios independientes
- Cada tienda tiene sus propios **productos, precios y ventas**
- Usuarios con acceso exclusivo a su tienda
- 4 tiendas preconfiguradas con datos de prueba

### 📦 **Gestión de Inventario**
- ➕ **Agregar productos** con categorías personalizadas
- ✏️ **Editar stock** y precios en tiempo real
- 🔍 **Buscar productos** por ID con respuesta en tiempo real
- 🗑️ **Eliminar productos** del inventario
- ⚠️ **Alertas de stock bajo** (menos de 5 unidades)

### 💰 **Gestión de Ventas**
- 💵 **Registrar ventas** desde el inventario
- 📊 **Historial completo** de ventas por tienda
- 📈 **Análisis** de productos más vendidos
- 💹 **Cálculo automático** de totales
- 📋 **Selector inteligente** de productos con stock visible

### 📊 **Dashboard y Reportes**
- 📈 **Gráficos interactivos** con Chart.js
- 🏆 **Top 5 productos** más vendidos
- ⚠️ **Alertas de stock bajo** con colores por nivel de criticidad
- 📄 **Reportes en PDF** descargables con ReportLab

### 👥 **Gestión de Usuarios**
- 🔐 **Sistema de autenticación** seguro (Django Auth)
- 👑 **Panel de administración** para superusuarios
- 📧 **Registro de nuevos usuarios** con inventario automático
- 🛡️ **Roles**: Admin y Usuario

---

## 🛠️ Tecnologías

### **Backend**
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Django** | 4.2.7 | Framework web principal |
| **Django ORM** | - | Mapeo objeto-relacional |
| **MySQL** | 8.0 | Base de datos en producción |
| **SQLite** | - | Base de datos en desarrollo |
| **Gunicorn** | 21.2.0 | Servidor WSGI para producción |
| **ReportLab** | 4.0.4 | Generación de reportes PDF |
| **PyMySQL** | 1.1.0 | Conector MySQL para Python |

### **Frontend**
| Tecnología | Propósito |
|------------|-----------|
| **HTML5** | Estructura de páginas |
| **CSS3** | Estilos y diseño responsivo |
| **JavaScript** | Interactividad y dinámicas |
| **Chart.js** | Gráficos interactivos |
| **Django Templates** | Motor de plantillas |

### **Infraestructura**
| Tecnología | Propósito |
|------------|-----------|
| **Render** | Plataforma de despliegue |
| **Git** | Control de versiones |
| **GitHub** | Repositorio remoto |

---

## 🏗️ Arquitectura
┌─────────────────────────────────────────────────────────────────┐
│ CLIENTE (Browser) │
└─────────────────────────────┬───────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ RENDER (Web Service) │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Gunicorn (WSGI Server) │ │
│ └───────────────────────────────────────────────────────────┘ │
│ │ │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Django │ │
│ │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐ │ │
│ │ │ Models │ │ Views │ │ Urls │ │ Templates │ │ │
│ │ └─────────┘ └─────────┘ └─────────┘ └──────────────┘ │ │
│ └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ RENDER (MySQL Private Service) │
│ MySQL Database │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ usuarios │ inventarios │ productos │ ventas │ auth_user │ │
│ └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

text

---

## 📋 Requisitos Previos

### **Desarrollo Local**
- Python 3.10 o superior
- Pip (gestor de paquetes)
- Git
- (Opcional) MySQL Workbench para gestionar la BD

### **Producción (Render)**
- Cuenta en [Render.com](https://render.com)
- Cuenta en [GitHub](https://github.com)

---

## 🚀 Instalación Local

### **1. Clonar el Repositorio**

```bash
git clone https://github.com/tu-usuario/django-inventario.git
cd django-inventario
2. Crear y Activar Entorno Virtual
bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
3. Instalar Dependencias
bash
pip install -r requirements.txt
4. Configurar Variables de Entorno
bash
# Crear archivo .env
echo "SECRET_KEY=tu-clave-secreta-aqui" > .env
echo "DEBUG=True" >> .env
5. Ejecutar Migraciones
bash
python manage.py makemigrations
python manage.py migrate
6. Inicializar Datos de Prueba
bash
python manage.py init_db
7. Crear Superusuario
bash
python manage.py createsuperuser
8. Ejecutar Servidor Local
bash
python manage.py runserver
9. Acceder a la Aplicación
text
http://localhost:8000
🌐 Despliegue en Render
Paso 1: Crear Repositorio en GitHub
bash
git init
git add .
git commit -m "Proyecto Django Inventario"
git remote add origin https://github.com/tu-usuario/django-inventario.git
git push -u origin main
Paso 2: Crear Base de Datos MySQL en Render
En Render, selecciona "New +" → "Private Service"

Conecta el repositorio render-examples/mysql

Configura variables de entorno:

MYSQL_DATABASE: inventario

MYSQL_USER: admin

MYSQL_PASSWORD: (contraseña segura)

MYSQL_ROOT_PASSWORD: (contraseña segura)

Agrega un disco con Mount Path: /var/lib/mysql

Obtén la URL interna: Render te dará algo como mysql-xyz:3306

Paso 3: Desplegar la Aplicación
En Render, selecciona "New +" → "Web Service"

Conecta tu repositorio de GitHub

Configura:

Campo	Valor
Build Command	pip install -r requirements.txt
Start Command	./start.sh
Agrega variables de entorno:

Key	Value
DATABASE_URL	mysql://admin:contraseña@mysql-xyz:3306/inventario
SECRET_KEY	tu-clave-secreta-produccion
DEBUG	False
Paso 4: Desplegar
bash
# En Render, haz clic en "Manual Deploy" → "Deploy latest commit"
📁 Estructura del Proyecto
text
📁 django-inventario/
│
├── 📄 manage.py                     # Punto de entrada de Django
├── 📄 requirements.txt              # Dependencias del proyecto
├── 📄 start.sh                      # Script de inicio para Render
├── 📄 .env                          # Variables de entorno (local)
│
├── 📁 mysite/                       # Configuración principal
│   ├── __init__.py
│   ├── settings.py                  # Configuración del proyecto
│   ├── urls.py                      # URLs principales
│   └── wsgi.py                      # Configuración WSGI
│
├── 📁 inventario_app/               # Aplicación principal
│   ├── __init__.py
│   ├── admin.py                     # Configuración del panel admin
│   ├── apps.py                      # Configuración de la app
│   ├── models.py                    # Modelos de base de datos
│   ├── views.py                     # Lógica de negocio (controladores)
│   ├── urls.py                      # URLs de la app
│   ├── utils.py                     # Funciones auxiliares (PDF)
│   │
│   ├── 📁 management/               # Comandos personalizados
│   │   └── 📁 commands/
│   │       └── init_db.py           # Inicialización de datos
│   │
│   └── 📁 templates/                # Plantillas HTML
│       └── 📁 inventario_app/
│           ├── login.html
│           ├── register.html
│           ├── index.html
│           ├── ventas.html
│           ├── dashboard.html
│           └── admin.html
│
├── 📁 static/                       # Archivos estáticos
│   ├── style.css                    # Estilos CSS
│   └── logo.png                     # Logo de la aplicación
│
└── 📁 media/                        # Archivos subidos (usuarios)
🗄️ Base de Datos
Modelo Entidad-Relación
text
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│     Usuario     │      │   Inventario    │      │    Producto     │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│ id (PK)         │      │ id (PK)         │      │ id (PK)         │
│ username        │      │ nombre          │──────│ nombre          │
│ email           │──────│                 │      │ categoria       │
│ password        │      │                 │      │ cantidad        │
│ is_superuser    │      │                 │      │ precio          │
└─────────────────┘      └─────────────────┘      │ inventario_id (FK)│
         │                                         └─────────────────┘
         │                                                  │
         │                                                  │
┌────────▼────────┐                                 ┌───────▼───────┐
│ UsuarioInventario│                                 │     Venta     │
├─────────────────┤                                 ├───────────────┤
│ usuario (FK)    │                                 │ id (PK)       │
│ inventario (FK) │                                 │ producto      │
└─────────────────┘                                 │ cantidad      │
                                                    │ precio        │
                                                    │ fecha         │
                                                    │ inventario_id (FK)│
                                                    └───────────────┘
🔌 API Endpoints
Autenticación
Método	Endpoint	Descripción
GET/POST	/login/	Inicio de sesión
GET/POST	/register/	Registro de usuario
GET	/logout/	Cierre de sesión
Inventario
Método	Endpoint	Descripción
GET	/index/	Página de inventario
POST	/agregar_producto/	Agregar nuevo producto
GET	/delete/<int:id>/	Eliminar producto
POST	/sumar/<int:id>/	Sumar stock
POST	/vender/<int:id>/	Vender desde inventario
Ventas
Método	Endpoint	Descripción
GET	/ventas/	Historial de ventas
POST	/venta/	Registrar nueva venta
Dashboard
Método	Endpoint	Descripción
GET	/dashboard/	Panel de control
GET	/reporte_pdf/	Descargar reporte PDF
Administración
Método	Endpoint	Descripción
GET	/admin_panel/	Panel de administración
POST	/crear_usuario_admin/	Crear usuario admin
GET	/eliminar_usuario/<int:id>/	Eliminar usuario
🔐 Variables de Entorno
Desarrollo Local (.env)
env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
Producción (Render)
Variable	Descripción	Ejemplo
DATABASE_URL	URL de conexión a MySQL	mysql://admin:pass@mysql-xyz:3306/inventario
SECRET_KEY	Clave secreta de Django	django-insecure-xyz...
DEBUG	Modo depuración	False
