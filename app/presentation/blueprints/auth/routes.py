"""
app/presentation/blueprints/auth/routes.py - Controlador de Autenticación
===========================================================================
Responsabilidad: Gestiona las rutas HTTP relacionadas con el acceso al sistema:
inicio de sesión (login) y cierre de sesión (logout).

Blueprint registrado como: "auth"
Prefijo de URL: (ninguno, raíz)

Rutas expuestas:
    GET  /          → Muestra el formulario de login.
    POST /          → Procesa las credenciales del formulario de login.
    GET  /logout    → Cierra la sesión activa y redirige al login.

Plantilla utilizada:
    - login.html: Formulario con campos `username` y `password`.

Flujo de Login (POST /):
    1. El usuario envía el formulario con username y password.
    2. Se llama a `AuthService.login()` que verifica en la DB.
    3. Si el login es exitoso:
       a. Se guardan `user_id`, `username` y `rol` en `flask.session`.
       b. Se redirige al Dashboard principal.
    4. Si el login falla:
       a. Se renderiza el formulario de nuevo con el mensaje de error.

Comportamiento especial en GET /:
    Si el usuario ya tiene sesión activa y navega a "/" (ej. volvió atrás),
    la sesión se limpia (`session.clear()`) para forzar un nuevo login limpio.
    Esto evita problemas con sesiones "obsoletas" al iniciar una nueva sesión.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from app.application.services.auth_service import AuthService

# Definición del Blueprint.
# `template_folder="templates"` indica que las plantillas de este blueprint
# están en `app/presentation/blueprints/auth/templates/`.
auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates"
)


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    """
    Vista principal de login. Maneja tanto la visualización del formulario (GET)
    como el procesamiento de las credenciales enviadas (POST).

    GET /: Si ya existe una sesión activa, se limpia para evitar conflictos
           con sesiones previas. Renderiza el formulario de login.

    POST /: Toma `username` y `password` del formulario y los valida.
            - Éxito: Crea la sesión y redirige al dashboard.
            - Fallo: Vuelve a renderizar el formulario con el error.

    Returns:
        Response: Renderizado de `login.html` (GET/POST fallido) o
                  redirección a `dashboard.home` (POST exitoso).
    """
    # Si ya hay sesión, limpiarla para permitir un login fresco
    if "user_id" in session:
        session.clear()

    error = None  # Variable para pasar el mensaje de error a la plantilla

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Delegar la validación al servicio de autenticación
        result = AuthService.login(username, password)

        if result["success"]:
            # Guardar datos del usuario en la sesión de Flask (cookie cifrada)
            session["user_id"] = result["user_id"]
            session["username"] = result["username"]
            session["rol"] = result["rol"]

            # Redirigir al panel principal
            return redirect(url_for("dashboard.home"))
        else:
            # Login fallido: pasar el error a la plantilla para mostrarlo
            error = result["error"]

    # GET o POST fallido: mostrar el formulario (con error si aplica)
    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    """
    Cierra la sesión del usuario autenticado.

    Elimina TODOS los datos de la sesión de Flask (user_id, username, rol),
    invalidando efectivamente el acceso. Después redirige al login.

    No requiere @login_required porque no tiene sentido proteger el logout:
    si no hay sesión, simplemente redirige al login de todas formas.

    Returns:
        Response: Redirección a `auth.login` (la página de inicio de sesión).
    """
    session.clear()  # Elimina todos los valores almacenados en la sesión activa
    return redirect(url_for("auth.login"))
