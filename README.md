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

---


---

## 📋 Requisitos Previos

### **Desarrollo Local**
- Python 3.10 o superior
- Pip (gestor de paquetes)
- Git
- (Opcional) MySQL Workbench para gestionar la BD

### **Producción (Render + Aiven)**
- Cuenta en [Render.com](https://render.com)
- Cuenta en [Aiven.io](https://aiven.io) (gratis)
- Cuenta en [GitHub](https://github.com)

---

## 🚀 Instalación Local

### **1. Clonar el Repositorio**

```bash
git clone https://github.com/tu-usuario/django-inventario.git
cd django-inventario
