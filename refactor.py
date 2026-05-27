import os
import shutil

BASE_DIR = r"d:\Camilo\APP\proyectoGrado\CAMBRI\app"

def create_dirs():
    dirs = [
        "presentation/blueprints",
        "application/services",
        "infrastructure/repositories",
        "core"
    ]
    for d in dirs:
        path = os.path.join(BASE_DIR, *d.split('/'))
        os.makedirs(path, exist_ok=True)

def move_files():
    # 1. Move Blueprints
    blueprints = ["auth", "dashboard", "empleados", "inventarios", "pedidos", "produccion", "reportes"]
    for bp in blueprints:
        src = os.path.join(BASE_DIR, bp)
        dst = os.path.join(BASE_DIR, "presentation", "blueprints", bp)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"Moved {bp} to presentation/blueprints/")

    # 2. Move Services
    src_services = os.path.join(BASE_DIR, "services")
    if os.path.exists(src_services):
        for f in os.listdir(src_services):
            if f.endswith(".py"):
                shutil.move(os.path.join(src_services, f), os.path.join(BASE_DIR, "application", "services", f))
        shutil.rmtree(src_services)
        print("Moved services to application/services/")

    # 3. Move Infrastructure
    src_db = os.path.join(BASE_DIR, "db.py")
    if os.path.exists(src_db):
        shutil.move(src_db, os.path.join(BASE_DIR, "infrastructure", "database.py"))
        print("Moved db.py to infrastructure/database.py")

    # 4. Move Models to Repositories
    src_models = os.path.join(BASE_DIR, "models")
    if os.path.exists(src_models):
        for f in os.listdir(src_models):
            if f.endswith("_model.py"):
                new_name = f.replace("_model.py", "_repository.py")
                shutil.move(os.path.join(src_models, f), os.path.join(BASE_DIR, "infrastructure", "repositories", new_name))
        shutil.rmtree(src_models)
        print("Moved models to infrastructure/repositories/")

    # 5. Move Core
    src_config = os.path.join(BASE_DIR, "config.py")
    if os.path.exists(src_config):
        shutil.move(src_config, os.path.join(BASE_DIR, "core", "config.py"))
        print("Moved config.py to core/config.py")
        
    src_utils = os.path.join(BASE_DIR, "utils.py")
    if os.path.exists(src_utils):
        shutil.move(src_utils, os.path.join(BASE_DIR, "core", "security.py"))
        print("Moved utils.py to core/security.py")
        
    # Create empty init for core, application, infrastructure, presentation
    for d in ["core", "application", "infrastructure", "presentation", "presentation/blueprints", "infrastructure/repositories", "application/services"]:
        init_path = os.path.join(BASE_DIR, *d.split('/'), "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("")

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = content
    
    # Imports
    new_content = new_content.replace("app.models.pedido_model", "app.infrastructure.repositories.pedido_repository")
    new_content = new_content.replace("app.models.cliente_model", "app.infrastructure.repositories.cliente_repository")
    new_content = new_content.replace("app.models.material_model", "app.infrastructure.repositories.material_repository")
    new_content = new_content.replace("app.models.usuario_model", "app.infrastructure.repositories.usuario_repository")
    new_content = new_content.replace("app.models.movimiento_model", "app.infrastructure.repositories.movimiento_repository")
    new_content = new_content.replace("app.models.produccion_model", "app.infrastructure.repositories.produccion_repository")
    new_content = new_content.replace("app.models.reporte_model", "app.infrastructure.repositories.reporte_repository")
    
    new_content = new_content.replace("app.models.", "app.infrastructure.repositories.")
    
    new_content = new_content.replace("app.services.auth_service", "app.application.services.auth_service")
    new_content = new_content.replace("app.services.dashboard_service", "app.application.services.dashboard_service")
    new_content = new_content.replace("app.services.empleado_service", "app.application.services.empleado_service")
    new_content = new_content.replace("app.services.inventario_service", "app.application.services.inventario_service")
    new_content = new_content.replace("app.services.pedido_service", "app.application.services.pedido_service")
    new_content = new_content.replace("app.services.produccion_service", "app.application.services.produccion_service")
    new_content = new_content.replace("app.services.reporte_service", "app.application.services.reporte_service")
    
    new_content = new_content.replace("app.db", "app.infrastructure.database")
    new_content = new_content.replace("app.utils", "app.core.security")
    
    # Class names
    new_content = new_content.replace("PedidoModel", "PedidoRepository")
    new_content = new_content.replace("ClienteModel", "ClienteRepository")
    new_content = new_content.replace("MaterialModel", "MaterialRepository")
    new_content = new_content.replace("UsuarioModel", "UsuarioRepository")
    new_content = new_content.replace("MovimientoModel", "MovimientoRepository")
    new_content = new_content.replace("ProduccionModel", "ProduccionRepository")
    new_content = new_content.replace("ReporteModel", "ReporteRepository")
    
    # __init__.py specifics
    if filepath.endswith("__init__.py") and "create_app" in new_content:
        new_content = new_content.replace("from .config import Config", "from app.core.config import Config")
        new_content = new_content.replace("from .auth.routes", "from app.presentation.blueprints.auth.routes")
        new_content = new_content.replace("from .dashboard.routes", "from app.presentation.blueprints.dashboard.routes")
        new_content = new_content.replace("from .pedidos.routes", "from app.presentation.blueprints.pedidos.routes")
        new_content = new_content.replace("from .inventarios.routes", "from app.presentation.blueprints.inventarios.routes")
        new_content = new_content.replace("from .produccion.routes", "from app.presentation.blueprints.produccion.routes")
        new_content = new_content.replace("from .reportes.routes", "from app.presentation.blueprints.reportes.routes")
        new_content = new_content.replace("from .empleados.routes", "from app.presentation.blueprints.empleados.routes")
        
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

def update_all_files():
    for root, dirs, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith(".py"):
                process_file(os.path.join(root, f))
                
    # Also check check_db.py in root
    check_db = r"d:\Camilo\APP\proyectoGrado\CAMBRI\check_db.py"
    if os.path.exists(check_db):
        process_file(check_db)

if __name__ == "__main__":
    create_dirs()
    move_files()
    update_all_files()
    print("Refactor completed.")
