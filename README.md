# 🏍️ Sistema de Gestión de Inventario para Talleres de Motos

![Django](https://shields.io)
![Python](https://shields.io)
![MySQL](https://shields.io)
![Render](https://shields.io)
![License](https://shields.io)

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
- [Variables de Entorno](#-variables-de-entorno)
- [Credenciales de Prueba](#-credenciales-de-prueba)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## 📖 Descripción

**Sistema de Gestión de Inventario** diseñado específicamente para talleres y tiendas de repuestos de motos. Permite administrar múltiples tiendas, cada una con su propio inventario independiente, gestionar productos, ventas, generar reportes y obtener análisis en tiempo real.

### 🎯 Propósito del Proyecto

Este proyecto fue desarrollado como **trabajo de grado** para la carrera de **Ingeniería de Sistemas**, demostrando la aplicación de tecnologías modernas en la resolución de problemas empresariales reales.

**Ideal para:**
- ✅ Talleres de mantenimiento de motos
- ✅ Tiendas de repuestos y accesorios
- ✅ Distribuidores de productos para motos
- ✅ Pequeñas y medianas empresas del sector automotriz

---

## ✨ Características

### 🏢 Multi-Tienda
- Gestión de **múltiples tiendas** con inventarios independientes.
- Cada tienda tiene sus propios **productos, precios y ventas**.
- Usuarios con acceso exclusivo a su tienda asignada.
- 4 tiendas preconfiguradas con datos de prueba automatizados.

### 📦 Gestión de Inventario
- ➕ **Agregar productos** con categorías personalizadas.
- ✏️ **Editar stock** y precios en tiempo real.
- 🔍 **Buscar productos** por ID con respuesta inmediata.
- 🗑️ **Eliminar productos** de forma lógica o física del inventario.
- ⚠️ **Alertas de stock bajo** (menos de 5 unidades).

### 💰 Gestión de Ventas
- 💵 **Registrar ventas** de forma directa desde el inventario.
- 📊 **Historial completo** de transacciones filtrado por tienda.
- 📈 **Análisis** automatizado de productos más vendidos.
- 💹 **Cálculo automático** de totales, impuestos y márgenes.

### 📊 Dashboard y Reportes
- 📈 **Gráficos interactivos** impulsados con Chart.js.
- 🏆 **Top 5 productos** con mayor demanda comercial.
- 📄 **Reportes en PDF** descargables generados dinámicamente con ReportLab.

### 👥 Gestión de Usuarios
- 🔐 **Autenticación segura** mediante Django Auth System.
- 👑 **Panel de administración** avanzado para superusuarios.
- 🛡️ **Roles definidos**: Administrador General y Usuario de Tienda.

---

## 🛠️ Tecnologías

### Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Django** | 4.2.7 | Framework web principal |
| **Django ORM** | - | Mapeo objeto-relacional |
| **MySQL** | 8.0 | Base de datos en producción |
| **SQLite** | - | Base de datos en desarrollo |
| **Gunicorn** | 21.2.0 | Servidor WSGI para producción |
| **ReportLab** | 4.0.4 | Generación de reportes PDF |
| **PyMySQL** | 1.1.0 | Conector MySQL para Python |

### Frontend

| Tecnología | Propósito |
|------------|-----------|
| **HTML5 / CSS3** | Estructura y diseño responsivo adaptado a móviles |
| **JavaScript** | Interactividad de la interfaz y peticiones asíncronas |
| **Chart.js** | Renderizado de gráficos estadísticos |
| **Django Templates** | Motor de renderizado del lado del servidor |

### Infraestructura

| Tecnología | Propósito |
|------------|-----------|
| **Render** | Plataforma de despliegue Cloud de la aplicación |
| **Aiven.io** | Hosting de la base de datos MySQL gestionada |
| **Git / GitHub**| Control de versiones y repositorio de código |

---

## 🏗️ Arquitectura

El sistema implementa una arquitectura web monolítica basada en el patrón **MVT (Modelo-Vista-Template)** nativo de Django:
- **Modelo (Model):** Gestiona la capa de datos y las relaciones de negocio (Tienda, Producto, Venta, Usuario) mediante Django ORM.
- **Vista (View):** Contiene la lógica de negocio, procesa las peticiones HTTP y conecta los modelos con las plantillas.
- **Plantilla (Template):** Capa de presentación que combina HTML estático con datos dinámicos inyectados por el backend.

---

## 📋 Requisitos Previos

### Desarrollo Local
- Python 3.10 o superior
- Pip (gestor de paquetes de Python)
- Git

### Producción (Cloud)
- Cuenta activa en [Render.com](https://render.com)
- Cuenta activa en [Aiven.io](https://aiven.io) (Nivel gratuito)

---

## 🚀 Instalación Local

 Sigue estos pasos para levantar el entorno de desarrollo local:

### 1. Clonar el Repositorio
```bash
git clone https://github.com
cd django-inventario
```

### 2. Crear y Activar el Entorno Virtual
```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crea un archivo llamado `.env` en la raíz del proyecto y añade el siguiente contenido:
```ini
SECRET_KEY=tu-clave-secreta-de-desarrollo-aqui
DEBUG=True
```

### 5. Ejecutar Migraciones de Base de Datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Inicializar Datos de Prueba (Comando Personalizado)
```bash
python manage.py init_db
```

### 7. Crear Superusuario (Acceso Administrativo)
```bash
python manage.py createsuperuser
```

### 8. Iniciar el Servidor de Desarrollo
```bash
python manage.py runserver
```

### 9. Acceder a la Aplicación
Abre tu navegador web e ingresa a: `http://localhost:8000`

---

## 🌐 Despliegue en Render con Aiven

### Paso 1: Configurar MySQL en Aiven
1. Inicia sesión en **Aiven.io** y crea un nuevo proyecto.
2. Selecciona **MySQL** con el plan **Free (1GB)**.
3. Elige la región de la nube de tu preferencia (ej. AWS Oregon o la más cercana a Render).
4. Espera a que el estado cambie a `Running` y copia la **Service URI**. Será similar a esto:
   ```text
   mysql://avnadmin:CONTRASEÑA@HOST:PORT/defaultdb?ssl-mode=REQUIRED
   ```

### Paso 2: Subir el Proyecto a GitHub
```bash
git init
git add .
git commit -m "Deployment release para producción"
git remote add origin https://github.com
git push -u origin main
```

### Paso 3: Crear el Web Service en Render
1. En el dashboard de **Render**, haz clic en **New +** ➡️ **Web Service**.
2. Conecta tu repositorio de GitHub recién creado.
3. Completa los campos básicos de configuración:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `./start.sh`

### Paso 4: Configurar Variables de Entorno en Render
Dentro de la pestaña **Environment** de tu Web Service en Render, añade las siguientes llaves:

| Key | Value |
|---|---|
| `DATABASE_URL` | *Tu Service URI de Aiven obtenida en el Paso 1* |
| `SECRET_KEY` | *Una cadena aleatoria larga para producción* |
| `DEBUG` | `False` |
| `PYTHON_VERSION` | `3.10.12` |

Haz clic en **Save Changes** para iniciar el build automático.

### Paso 5: Inicializar URLs de Producción (Post-Despliegue)
Una vez que el servicio esté activo (`Live`), visita las siguientes rutas en orden para poblar tu base de datos cloud:
1. **Crear base de administración:** `https://onrender.com`
2. **Iniciar sesión en la plataforma:** `https://onrender.com`
3. **Poblar las tiendas y catálogos:** `https://onrender.com`

---

## 📁 Estructura del Proyecto

```text
📁 django-inventario/
│
├── 📄 manage.py                     # Punto de entrada de la CLI de Django
├── 📄 requirements.txt              # Archivo de dependencias del proyecto
├── 📄 start.sh                      # Script ejecutable de arranque para Render
├── 📄 .env                          # Variables de entorno locales (Ignorado en Git)
│
├── 📁 mysite/                       # Directorio de configuración global del proyecto
│   ├── __init__.py
│   ├── settings.py                  # Ajustes de bases de datos, seguridad y apps
│   ├── urls.py                      # Enrutador de URLs global
│   └── wsgi.py                      # Interfaz de servidor web compatible con Gunicorn
│
└── 📁 inventario_app/               # Aplicación core del sistema de inventario
    ├── __init__.py
    ├── admin.py                     # Registro de modelos en el panel de Django
    ├── apps.py                      # Configuración modular de la app
    ├── models.py                    # Esquemas de la base de datos (ORM)
    ├── views.py                     # Controladores de lógica y respuestas HTTP
    ├── urls.py                      # Rutas internas de la aplicación
    ├── utils.py                     # Funciones auxiliares (ej. Generación de PDFs)
    │
    ├── 📁 management/               # Comandos de consola personalizados de Django
    │   └── 📁 commands/
