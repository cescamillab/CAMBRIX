# CAMBRIX - Sistema de Gestión y Dashboard Analítico

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-black.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)

## 📖 Descripción General del Proyecto
**CAMBRIX** (Proyecto Chamba) es una plataforma integral desarrollada en Python (Flask) diseñada para la gestión, control y análisis operativo de la empresa. Integra en una sola herramienta la administración de inventarios, pedidos, producción, clientes, empleados y generación de reportes financieros y operativos.

### 🎯 Objetivo y Problema que Resuelve
Muchas empresas manejan su información operativa de forma fragmentada, usando hojas de cálculo o software genérico que no se adapta a su flujo real. **CAMBRIX resuelve la falta de trazabilidad y descontrol en la producción e inventarios**, centralizando:
- Control preciso del stock de materiales y su consumo en producción.
- Seguimiento de los pedidos desde la cotización hasta la entrega.
- Emisión de reportes automáticos en PDF y Excel para toma de decisiones.

---

## 🏗 Arquitectura del Sistema

El sistema implementa una arquitectura por capas, inspirada en **Clean Architecture (Arquitectura Limpia)** y adaptada a Flask, para separar responsabilidades y facilitar el mantenimiento.

### Capas Principales:
1. **Presentation (Presentación):** Contiene los *Blueprints* de Flask, las rutas (Controladores) y las vistas (HTML/Jinja2).
2. **Application (Aplicación):** Contiene los *Servicios* con la lógica de negocio, reglas de validación y flujos de trabajo.
3. **Core (Núcleo):** Configuraciones globales, seguridad y variables de entorno.
4. **Infrastructure (Infraestructura):** Conexión a la base de datos (MySQL) y *Repositorios* que encapsulan todas las consultas SQL.

### 📂 Estructura Completa de Carpetas y Archivos
```text
/CAMBRI
├── app/                        # Lógica principal de la aplicación
│   ├── application/            # Capa de Lógica de Negocio (Servicios)
│   │   └── services/           # (auth_service, pedido_service, inventario_service, etc.)
│   ├── core/                   # Configuraciones centrales
│   │   ├── config.py           # Carga de variables de entorno
│   │   └── security.py         # Manejo de roles y autenticación
│   ├── infrastructure/         # Capa de Acceso a Datos
│   │   ├── database.py         # Conector a MySQL
│   │   └── repositories/       # Consultas SQL (pedido_repository, material_repository, etc.)
│   ├── presentation/           # Capa de Presentación (Rutas y Vistas)
│   │   └── blueprints/         # Módulos HTTP (auth, dashboard, pedidos, etc.)
│   ├── static/                 # Assets (CSS Vanilla, JS, Imágenes)
│   ├── templates/              # Plantillas Jinja2
│   └── __init__.py             # Factory de la aplicación Flask
├── docs/                       # Manuales adicionales (Usuario, Técnico, Instalación, etc.)
├── venv/                       # Entorno virtual de Python
├── .env                        # Variables de entorno sensibles (No versionado)
├── requirements.txt            # Dependencias del proyecto
├── run.py                      # Punto de entrada para levantar el servidor
└── CAMBRI.bat                  # Script de ejecución para Windows
```

---

## 🛠 Tecnologías Utilizadas

- **Backend:** Python 3.8+, Flask 3.0 (Elegido por su ligereza y control granular sobre la arquitectura).
- **Base de Datos:** MySQL 8.0 y `mysql-connector-python` (Base de datos relacional ideal para trazabilidad financiera y de inventario).
- **Frontend:** HTML5, CSS3 Vanilla, JavaScript, Bootstrap 5.3 (Para UI responsive).
- **Visualización:** Chart.js 4.0 (Para el dashboard interactivo).
- **Generación de Reportes:** `pandas`, `openpyxl` (Excel), `reportlab` (PDF).

---

## ⚙️ Flujo de Funcionamiento del Sistema

1. **Autenticación:** El usuario (Jefe o Empleado) inicia sesión.
2. **Navegación:** Dependiendo de su rol, el usuario accede a diferentes módulos (Dashboard, Pedidos, Inventarios).
3. **Petición HTTP:** Cuando el usuario interactúa (ej. "Crear Pedido"), el **Blueprint** correspondiente recibe la petición.
4. **Lógica de Negocio:** El Blueprint llama a la capa **Application (Service)**, donde se aplican las reglas (ej. validar si hay stock suficiente).
5. **Persistencia:** El Servicio llama a la capa **Infrastructure (Repository)**, que ejecuta las sentencias SQL para leer/guardar en MySQL.
6. **Respuesta:** La información viaja de regreso y se renderiza en una plantilla **Jinja2**.

---

## 📦 Módulos y Componentes

1. **Auth:** Manejo de sesiones y login. Protege rutas con `@login_required`.
2. **Dashboard:** Pantalla principal con KPIs, gráficas y estado general de la empresa.
3. **Pedidos:** Registro, actualización y seguimiento del estado de las ventas o servicios.
4. **Inventarios:** Control de ingresos/salidas de materiales, alertas de stock bajo y registro de movimientos históricos.
5. **Producción:** Asignación de materiales a pedidos específicos (Trazabilidad de qué insumos se gastaron en cada trabajo).
6. **Empleados:** Gestión de personal, creación de usuarios y roles de acceso.
7. **Reportes:** Motor de exportación de datos a PDF y Excel para auditorías.

---

## 🚀 Guía de Instalación y Ejecución

### Requisitos Previos
- Python 3.8 o superior.
- MySQL Server en ejecución.

### 1. Variables de Entorno (.env)
Crea un archivo `.env` en la raíz del proyecto (al nivel de `run.py`) con el siguiente formato:
```env
SECRET_KEY=tu_clave_secreta_super_segura_123
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=cambri_db
```

### 2. Configuración de la Base de Datos
Debes crear la base de datos `cambri_db` en tu gestor de MySQL.
*(Las tablas se crearán utilizando el script SQL o migraciones correspondientes si existen en los manuales de DB).*

### 3. Instalación Paso a Paso (Desarrollo)

**Paso 1:** Clonar el proyecto y entrar a la carpeta.
```bash
git clone <url-repositorio>
cd CAMBRI
```

**Paso 2:** Crear y activar entorno virtual.
- **Windows:** `python -m venv venv` y luego `.\venv\Scripts\activate`
- **Linux/Mac:** `python3 -m venv venv` y luego `source venv/bin/activate`

**Paso 3:** Instalar dependencias.
```bash
pip install -r requirements.txt
```

**Paso 4:** Ejecutar el servidor.
```bash
python run.py
```
> La aplicación estará corriendo en [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

### Scripts Disponibles
- `run.py`: Levanta el servidor de desarrollo en Flask.
- `CAMBRI.bat`: Script para levantar el entorno y el servidor automáticamente en Windows con doble clic.

---

## 🔒 Autenticación y Seguridad

- **Manejo de Sesiones:** Se utilizan las sesiones nativas de Flask (`session`), cifradas usando `SECRET_KEY`.
- **Roles:** El sistema diferencia entre `jefe` (acceso total a configuración y reportes) y `empleado` (acceso limitado a operativas diarias).
- **Protección de Caché:** El archivo `app/__init__.py` inyecta cabeceras de no-caché en respuestas HTTP para prevenir que los usuarios vean páginas seguras después de cerrar sesión usando el botón "Atrás".

---

## 💾 Modelos de Datos y Relaciones

El esquema relacional base (`cambri_db`) comprende las siguientes entidades clave:
- **usuarios**: (`id`, `username`, `password_hash`, `rol`)
- **clientes**: Información de contacto y facturación.
- **pedidos**: Relaciona cliente, fechas, estado y valor.
- **materiales**: Catálogo de stock.
- **movimientos_inventario**: Historial de entradas/salidas (Auditoría de almacén).
- **produccion_materiales**: Tabla transaccional (Muchos a Muchos) que relaciona un `pedido` con los `materiales` consumidos en su producción.

---

## 🔌 APIs y Endpoints (Ejemplos)

Aunque la aplicación renderiza HTML (SSR), la estructura de rutas sigue patrones REST lógicos.

- **GET /pedidos/** : Muestra la lista de todos los pedidos.
- **POST /pedidos/crear** : Procesa el formulario para un nuevo pedido.
- **GET /inventarios/movimientos** : Historial de inventario.
- **POST /reportes/excel** : Descarga un archivo `.xlsx`.

*Ejemplo de Lógica Compleja:* **Consumo de Inventario en Producción**
Al registrar la producción (`produccion_service.py`), el sistema verifica si hay stock suficiente en `materiales`. Si lo hay, realiza el descuento en `materiales`, inserta el registro en `produccion_materiales` y deja una huella en `movimientos_inventario`. Toda esta operación debería ser transaccional.

---

## 🧪 Manejo de Errores y Testing

- **Errores:** Las excepciones de Base de Datos y de validación de negocio se capturan en la capa de *Servicios*, retornando mensajes comprensibles al *Blueprint*, el cual los muestra al usuario mediante mensajes **Flash** de Flask.
- **Testing:** Se recomienda la creación de un directorio `tests/` con pruebas unitarias usando `pytest` para probar de forma aislada los métodos de los servicios.

---

## 📌 Buenas Prácticas Implementadas

- **Separación de Responsabilidades:** Las consultas SQL jamás están en los controladores, siempre en `repositories/`.
- **Variables Sensibles Aisladas:** Uso estricto de `.env`.
- **Blueprints:** Modularidad que permite que el proyecto escale sin tener un solo archivo gigante de rutas.

## 🚀 Despliegue (Producción)

Para entornos de producción, **NUNCA** utilices el servidor nativo de Flask (`python run.py`). 
1. Utiliza un servidor WSGI como **Gunicorn** o **Waitress** (en Windows).
2. Usa un proxy inverso como **Nginx** o **Apache** para servir archivos estáticos (`/static`) y balancear la carga.
3. Asegúrate de configurar la variable de entorno `FLASK_ENV=production` y de mantener tu `SECRET_KEY` segura.

## 🔮 Mejoras Futuras y Limitaciones
- **Migración a ORM:** Reemplazar consultas SQL en crudo (`mysql-connector`) por **SQLAlchemy** para evitar inyección SQL más robustamente y agilizar el desarrollo.
- **API REST / JSON:** Separar completamente el Frontend (React/Vue) del Backend devolviendo únicamente JSON, mejorando el rendimiento.
- **Testing Automatizado:** Implementar cobertura con `pytest`.

---
*Para mayor detalle, consulta los manuales en la carpeta `/docs` del repositorio.*
