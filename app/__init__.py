"""
app/__init__.py - Factoría de la Aplicación Flask (Application Factory)
========================================================================
Este módulo define la función `create_app()`, que es el corazón del
proceso de inicialización de CAMBRIX.

¿Por qué el patrón Application Factory?
- Permite crear múltiples instancias de la aplicación con distintas
  configuraciones (desarrollo, testing, producción) sin conflictos.
- Facilita las pruebas unitarias al poder crear una app "limpia" por test.
- Evita el problema de importaciones circulares al diferir la creación
  del objeto `app` hasta que sea necesario.
"""
from flask import Flask
from app.core.config import Config


def create_app():
    """
    Crea, configura y retorna una instancia completamente inicializada de Flask.

    Pasos que realiza:
    1. Instancia Flask con el nombre del paquete actual.
    2. Carga la configuración desde el objeto `Config` (que lee las variables de .env).
    3. Importa y registra cada Blueprint (módulo de rutas) en la aplicación.
    4. Define un hook `after_request` para deshabilitar el caché del navegador.

    Returns:
        Flask: La instancia de la aplicación Flask lista para servir peticiones.
    """
    app = Flask(__name__)

    # Carga la configuración centralizada desde `app/core/config.py`.
    # Esto inyecta SECRET_KEY, DB_HOST, DB_USER, DB_PASSWORD y DB_NAME en app.config.
    app.config.from_object(Config)

    # -----------------------------------------------------------------------
    # Registro de Blueprints
    # -----------------------------------------------------------------------
    # Cada Blueprint es un módulo independiente con sus propias rutas, templates
    # y lógica. Se importan DENTRO de la función para evitar importaciones
    # circulares (una práctica estándar con Flask).
    from app.presentation.blueprints.auth.routes import auth_bp
    from app.presentation.blueprints.dashboard.routes import dashboard_bp
    from app.presentation.blueprints.pedidos.routes import pedidos_bp
    from app.presentation.blueprints.inventarios.routes import inventarios_bp
    from app.presentation.blueprints.produccion.routes import produccion_bp
    from app.presentation.blueprints.reportes.routes import reportes_bp
    from app.presentation.blueprints.empleados.routes import empleados_bp

    # Registrar cada Blueprint en la aplicación principal.
    # Los prefijos de URL (url_prefix) están definidos dentro de cada Blueprint.
    app.register_blueprint(auth_bp)         # Rutas: /  y  /logout
    app.register_blueprint(dashboard_bp)    # Rutas: /dashboard/
    app.register_blueprint(pedidos_bp)      # Rutas: /pedidos/...
    app.register_blueprint(inventarios_bp)  # Rutas: /inventarios/...
    app.register_blueprint(produccion_bp)   # Rutas: /produccion/...
    app.register_blueprint(reportes_bp)     # Rutas: /reportes/...
    app.register_blueprint(empleados_bp)    # Rutas: /empleados/...

    # -----------------------------------------------------------------------
    # Hook de Seguridad: Deshabilitar Caché del Navegador
    # -----------------------------------------------------------------------
    @app.after_request
    def add_header(response):
        """
        Se ejecuta DESPUÉS de cada petición HTTP antes de enviar la respuesta.

        Propósito: Inyecta cabeceras HTTP que instruyen al navegador a NO
        almacenar en caché ninguna página. Esto es crítico para la seguridad:
        sin esto, un usuario podría presionar el botón "Atrás" del navegador
        después de cerrar sesión y ver páginas protegidas desde el caché local.

        Args:
            response: El objeto de respuesta HTTP de Flask.

        Returns:
            response: La misma respuesta con las cabeceras de no-caché añadidas.
        """
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
