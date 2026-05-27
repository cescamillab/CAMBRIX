"""
app/core/security.py - Decoradores de Seguridad y Control de Acceso
=====================================================================
Este módulo centraliza la lógica de autenticación y autorización
que se aplica a las rutas de Flask mediante decoradores.

¿Qué es un decorador de ruta?
    Es una función que "envuelve" a otra función (la vista/controlador)
    para ejecutar lógica adicional ANTES de que la vista se ejecute.
    Se aplica con la sintaxis `@nombre_del_decorador` justo antes de la
    definición de la función de vista.

Ejemplo de uso:
    @inventarios_bp.route("/inventarios/")
    @login_required          # <-- Este decorador se aplica ANTES de ejecutar la vista
    def listar_materiales():
        ...
"""
from functools import wraps
from flask import session, redirect, url_for


def login_required(f):
    """
    Decorador que protege una ruta, requiriendo que el usuario haya iniciado sesión.

    Mecanismo:
        Verifica si la clave "user_id" existe en la sesión activa de Flask.
        La sesión es una cookie cifrada con SECRET_KEY que Flask gestiona automáticamente.
        Si el usuario no ha iniciado sesión, "user_id" no estará en la sesión.

    Comportamiento:
        - Si la sesión CONTIENE "user_id": La petición continúa normalmente
          y se ejecuta la función de vista original.
        - Si la sesión NO CONTIENE "user_id": El usuario es redirigido
          inmediatamente a la página de login (`/`), sin ejecutar la vista.

    Args:
        f (function): La función de vista de Flask que se quiere proteger.

    Returns:
        function: La función envuelta (`decorated_function`) que primero
                  verifica la sesión antes de ejecutar la vista original.

    Uso:
        @algún_blueprint.route("/ruta-protegida")
        @login_required
        def mi_vista():
            ...
    """
    @wraps(f)  # Preserva el nombre y docstring de la función original `f` (importante para Flask)
    def decorated_function(*args, **kwargs):
        # Comprueba si el usuario tiene una sesión activa válida
        if "user_id" not in session:
            # No hay sesión: redirigir a la página de login
            return redirect(url_for("auth.login"))
        # Hay sesión válida: ejecutar la vista original con sus argumentos
        return f(*args, **kwargs)
    return decorated_function
