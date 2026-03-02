from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registrar Blueprints
    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .pedidos.routes import pedidos_bp
    from .inventarios.routes import inventarios_bp
    from .produccion.routes import produccion_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(inventarios_bp)
    app.register_blueprint(produccion_bp)

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
