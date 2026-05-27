"""
app/presentation/blueprints/empleados/routes.py - Controlador de Empleados
============================================================================
Responsabilidad: Gestiona las rutas HTTP para la administración del personal
(usuarios del sistema). Todas las operaciones son exclusivas del rol "jefe".

Blueprint registrado como: "empleados"
Prefijo de URL: (ninguno, rutas directas /empleados/...)

Rutas expuestas:
    GET  /empleados              → Lista todos los empleados registrados.
    POST /empleados/crear        → Crea un nuevo empleado/usuario.
    POST /empleados/editar/<id>  → Edita los datos de un empleado.
    POST /empleados/eliminar/<id>→ Elimina un empleado del sistema.

Control de Acceso:
    Este Blueprint no usa `@login_required` ni `@role_required` del modo
    estándar. En cambio, define la función helper local `es_jefe()` que
    verifica el rol en la sesión. Cada vista llama a `es_jefe()` al inicio
    y redirige al dashboard si no se cumple la condición.

    NOTA TÉCNICA: Este patrón es funcionalmente equivalente a `@role_required`,
    pero se implementó de forma ad-hoc en este Blueprint. Para consistencia,
    se recomienda migrar al decorador `@role_required("jefe")` definido en
    `pedidos/routes.py`.

Manejo de Feedback al Usuario (Flash Messages):
    Después de cada operación (crear, editar, eliminar), se usa `flash()` para
    mostrar un mensaje al usuario en la siguiente página. Los tipos son:
    - "success": Operación exitosa (verde).
    - "danger":  Error en la operación (rojo).
    - "warning": Operación no completada por una regla de negocio (amarillo).

Plantillas utilizadas:
    - listar_empleados.html: Tabla con todos los empleados y formularios modales
                             integrados para crear y editar empleados.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.application.services.empleado_service import EmpleadoService

# Definición del Blueprint (sin url_prefix, las rutas empiezan con /empleados)
empleados_bp = Blueprint(
    "empleados",
    __name__,
    template_folder="templates"
)


def es_jefe():
    """
    Función helper que verifica si el usuario autenticado tiene rol de "jefe".

    Lee el rol desde `flask.session` (guardado al momento del login).
    Es una verificación rápida de rol usada como guardia en cada vista.

    Returns:
        bool: True si el rol en sesión es "jefe", False en cualquier otro caso
              (incluyendo "empleado" o si no hay sesión activa).
    """
    return session.get("rol") == "jefe"


@empleados_bp.route("/empleados")
def listar_empleados():
    """
    Muestra la lista completa de todos los empleados/usuarios del sistema.

    Acceso: Solo "jefe". Si un no-jefe intenta acceder, recibe un mensaje
    flash de error y es redirigido al dashboard.

    Returns:
        Response: Renderizado de `listar_empleados.html` con la lista de empleados,
                  o redirección al dashboard si no tiene permisos.
    """
    if not es_jefe():
        # Informar al usuario y redirigir al dashboard sin mostrar la vista
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("dashboard.home"))

    empleados = EmpleadoService.get_all_empleados()
    return render_template("listar_empleados.html", empleados=empleados)


@empleados_bp.route("/empleados/crear", methods=["POST"])
def crear_empleado():
    """
    Procesa el formulario de creación de un nuevo empleado/usuario.

    Solo acepta método POST (el formulario viene de un modal en `listar_empleados.html`).
    Extrae los campos del formulario y delega la creación al servicio.

    Campos del formulario esperados:
        - nombre   (str): Nombre completo del empleado.
        - username (str): Nombre de usuario único para el login.
        - password (str): Contraseña inicial.
        - rol      (str): Rol asignado ("jefe" o "empleado").

    Returns:
        Response: Redirección a `empleados.listar_empleados` con mensaje flash
                  indicando éxito o error.
    """
    if not es_jefe():
        return redirect(url_for("dashboard.home"))

    # Extraer datos del formulario (usar .get() para evitar KeyError si falta un campo)
    nombre = request.form.get("nombre")
    username = request.form.get("username")
    password = request.form.get("password")
    rol = request.form.get("rol")

    # El servicio valida los campos y retorna (éxito, mensaje)
    success, msg = EmpleadoService.create_empleado(nombre, username, password, rol)
    flash(msg, "success" if success else "danger")

    return redirect(url_for("empleados.listar_empleados"))


@empleados_bp.route("/empleados/editar/<int:id>", methods=["POST"])
def editar_empleado(id):
    """
    Procesa el formulario de edición de un empleado existente.

    Solo acepta método POST. La contraseña es opcional en la edición:
    si el campo viene vacío, el servicio conserva la contraseña actual.

    Args:
        id (int): ID del empleado a editar (capturado de la URL).

    Campos del formulario esperados:
        - nombre   (str):      Nuevo nombre completo.
        - username (str):      Nuevo nombre de usuario.
        - password (str|""):   Nueva contraseña (vacío = no cambiar).
        - rol      (str):      Nuevo rol ("jefe" o "empleado").

    Returns:
        Response: Redirección a `empleados.listar_empleados` con mensaje flash.
    """
    if not es_jefe():
        return redirect(url_for("dashboard.home"))

    nombre = request.form.get("nombre")
    username = request.form.get("username")
    # La contraseña puede ser vacía (no se cambia) o un nuevo valor
    password = request.form.get("password")
    rol = request.form.get("rol")

    success, msg = EmpleadoService.update_empleado(id, nombre, username, rol, password)
    flash(msg, "success" if success else "danger")

    return redirect(url_for("empleados.listar_empleados"))


@empleados_bp.route("/empleados/eliminar/<int:id>", methods=["POST"])
def eliminar_empleado(id):
    """
    Elimina un empleado del sistema.

    Solo acepta método POST (para evitar eliminaciones accidentales por GET).
    Pasa el `current_user_id` desde la sesión al servicio para aplicar la
    regla de negocio que impide el auto-borrado.

    Args:
        id (int): ID del empleado a eliminar (capturado de la URL).

    Lógica del tipo de flash:
        - "success": Eliminación exitosa.
        - "warning": Si el mensaje contiene "propia" (auto-borrado bloqueado).
        - "danger":  Cualquier otro error.

    Returns:
        Response: Redirección a `empleados.listar_empleados` con mensaje flash.
    """
    if not es_jefe():
        return redirect(url_for("dashboard.home"))

    # Pasar el ID del usuario actual para que el servicio pueda validar el auto-borrado
    success, msg = EmpleadoService.delete_empleado(id, session.get("user_id"))

    # Determinar el tipo de alerta según el contenido del mensaje
    flash(msg, "success" if success else ("warning" if "propia" in msg else "danger"))

    return redirect(url_for("empleados.listar_empleados"))
