from flask import Flask
from app.core.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registrar Blueprints
    from app.presentation.blueprints.auth.routes import auth_bp
    from app.presentation.blueprints.dashboard.routes import dashboard_bp
    from app.presentation.blueprints.pedidos.routes import pedidos_bp
    from app.presentation.blueprints.inventarios.routes import inventarios_bp
    from app.presentation.blueprints.produccion.routes import produccion_bp
    from app.presentation.blueprints.reportes.routes import reportes_bp
    from app.presentation.blueprints.empleados.routes import empleados_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(inventarios_bp)
    app.register_blueprint(produccion_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(empleados_bp)

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
