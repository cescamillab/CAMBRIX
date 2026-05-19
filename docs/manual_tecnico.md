# Manual Técnico - CAMBRI

Este manual está dirigido a desarrolladores y personal técnico encargado de dar soporte o extender las funcionalidades de la plataforma **CAMBRI**.

## 1. Arquitectura del Sistema

El sistema utiliza una arquitectura basada en el patrón **MVC (Modelo-Vista-Controlador)** simplificado, implementado con el framework **Flask** (Python).

### 1.1 Estructura de Directorios
```text
/CAMBRI
├── app/                # Lógica principal de la aplicación
│   ├── auth/           # Módulo de autenticación
│   ├── dashboard/      # Panel de control y analítica
│   ├── pedidos/        # Gestión de pedidos de clientes
│   ├── inventarios/    # Control de stock y materiales
│   ├── produccion/     # Gestión de transformación y uso de insumos
│   ├── reportes/       # Generación de archivos Excel y PDF
│   ├── static/         # Archivos CSS, imágenes y JS
│   ├── templates/      # Plantillas HTML base
│   └── db.py           # Configuración de conexión MySQL
├── docs/               # Documentación técnica y de usuario
├── run.py              # Punto de entrada de la aplicación
└── .env                # Configuración de variables sensibles
```

### 1.2 Flujo de Datos
1. El usuario realiza una petición HTTP desde el navegador.
2. El servidor Flask (organizado por **Blueprints**) recibe la petición en `routes.py`.
3. Se interactúa con la base de datos MySQL a través del módulo `app/db.py`.
4. Los datos se procesan y se renderizan en plantillas HTML dinámicas usando el motor **Jinja2**.

---

## 2. Tecnologías Utilizadas

- **Backend:** Python 3.12, Flask 3.0.
- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript, Bootstrap 5.3.
- **Gráficas:** Chart.js 4.0.
- **Generación de Archivos:** 
  - Excel: `pandas`, `openpyxl`.
  - PDF: `reportlab`.
- **Base de Datos:** MySQL 8.0.

---

## 3. Diccionario de Datos (Resumen de Tablas)

El sistema opera sobre la base de datos `cambri_db`. Las tablas principales son:

| Tabla | Función |
| :--- | :--- |
| `usuarios` | Almacena las credenciales y roles (`jefe`, `empleado`). |
| `clientes` | Información de contacto de los clientes de Cambri. |
| `pedidos` | Encabezado de los pedidos, valores totales y estados. |
| `materiales` | Catálogo de insumos en el inventario con stock actual. |
| `produccion_materiales` | Detalle de qué materiales se usaron en qué pedido (Trazabilidad). |
| `movimientos_inventario` | Registro histórico de entradas y salidas de stock. |

---

## 4. Estándares de Desarrollo

### Seguridad
- Las contraseñas se gestionan de forma segura (actualmente bajo validación de sesión en Flask).
- El sistema incluye un decorador `@login_required` para proteger rutas sensibles.
- Se implementan roles de usuario para restringir acciones administrativas (solo `jefe`).

### Interfaz (UI)
- Se utiliza un sistema de diseño propio definido en `app/static/css/style.css`.
- Los colores corporativos son: **Azul (#029EF2)**, Blanco y Negro.
- Uso extensivo de **Bootstrap Icons** para la representación visual de acciones.

---

## 5. Mantenibilidad y Extensibilidad
El sistema está diseñado de forma modular mediante **Blueprints**. Para agregar un nuevo módulo:
1. Crear una carpeta dentro de `app/`.
2. Definir un archivo `routes.py` y una carpeta `templates/`.
3. Registrar el nuevo Blueprint en `app/__init__.py`.
