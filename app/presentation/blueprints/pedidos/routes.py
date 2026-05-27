"""
app/presentation/blueprints/pedidos/routes.py - Controlador de Pedidos
========================================================================
Responsabilidad: Gestiona todas las rutas HTTP del módulo de pedidos:
listado con filtros, creación, detalle, edición, cambio de estado y eliminación.

Blueprint registrado como: "pedidos"
Prefijo de URL: /pedidos

Rutas expuestas:
    GET      /pedidos/                           → Lista de pedidos (con filtros).
    GET/POST /pedidos/crear                      → Formulario de nuevo pedido.
    POST     /pedidos/actualizar_estado/<id>     → Cambiar estado de un pedido.
    GET      /pedidos/<id>                       → Detalle completo de un pedido.
    GET/POST /pedidos/editar/<id>                → Formulario de edición de pedido.
    POST     /pedidos/eliminar/<id>              → Eliminar un pedido.

Control de Acceso Mixto:
    Este Blueprint implementa dos niveles de control:
    1. `@login_required`: Para rutas que cualquier usuario autenticado puede ver
       (listar, ver detalle, cambiar estado).
    2. `@role_required("jefe")`: Para rutas exclusivas del jefe (crear, editar, eliminar).
       Este decorador usa `abort(403)` en lugar de redirigir, generando una
       página de error 403 si un empleado intenta acceder directamente por URL.

Decorador `role_required`:
    Es un decorador parametrizado (factory de decoradores) definido localmente.
    Toma el rol requerido como argumento y retorna el decorador correspondiente.
    A diferencia del helper `es_jefe()` del Blueprint de empleados, este usa
    `abort(403)` que es el estándar HTTP para acceso denegado.

Plantillas utilizadas:
    - lista_pedidos.html:   Tabla de pedidos con filtros, búsqueda y ordenamiento.
    - crear_pedidos.html:   Formulario de creación (cliente nuevo o existente).
    - detalle_pedido.html:  Vista de detalle con info del cliente y materiales usados.
    - editar_pedido.html:   Formulario de edición pre-poblado.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from functools import wraps
from app.core.security import login_required
from app.application.services.pedido_service import PedidoService

# Definición del Blueprint con prefijo /pedidos
pedidos_bp = Blueprint(
    "pedidos",
    __name__,
    url_prefix="/pedidos",
    template_folder="templates"
)


def role_required(role):
    """
    Decorador factory que protege una ruta para un rol específico.

    Genera un decorador que verifica si el usuario en sesión tiene el
    rol requerido. Si no lo tiene, llama a `abort(403)` que Flask convierte
    en una respuesta HTTP 403 Forbidden.

    Diferencia con `es_jefe()` del blueprint de empleados:
        - `es_jefe()` redirige al dashboard.
        - `role_required()` retorna un error HTTP 403 (más apropiado para
          accesos directos por URL a rutas protegidas).

    Args:
        role (str): El rol requerido para acceder a la ruta. Ej: "jefe".

    Returns:
        function: El decorador que envuelve la función de vista.

    Uso:
        @pedidos_bp.route("/crear")
        @login_required
        @role_required("jefe")
        def crear_pedido():
            ...
    """
    def decorator(f):
        @wraps(f)  # Preservar metadatos de la función original
        def decorated_function(*args, **kwargs):
            if session.get("rol") != role:
                abort(403)  # HTTP 403: Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ===========================================================================
# LISTAR PEDIDOS (con filtros dinámicos)
# ===========================================================================
@pedidos_bp.route("/")
@login_required
def listar_pedidos():
    """
    Muestra la lista de pedidos con soporte para filtros, búsqueda y ordenamiento.

    Accesible para todos los usuarios autenticados. El servicio se encarga de
    filtrar automáticamente por `responsable_id` para los empleados.

    Query Parameters (todos opcionales):
        busqueda    (str): Búsqueda por nombre de cliente.
        estado      (str): Filtro por estado ("pendiente", "en_proceso", "terminado").
        responsable (str): ID del responsable (solo aplica para el jefe).
        fecha_inicio(str): Fecha de entrega mínima 'YYYY-MM-DD'.
        fecha_fin   (str): Fecha de entrega máxima 'YYYY-MM-DD'.
        orden_id    (str): Ordenar por ID ("asc" o "desc").
        orden_fecha (str): Ordenar por fecha de entrega ("asc" o "desc").

    Variables enviadas a la plantilla:
        - pedidos:      Lista de pedidos filtrados.
        - busqueda, estado, responsable, fecha_inicio, fecha_fin,
          orden_id, orden_fecha: Para mantener el estado de los filtros en la UI.
        - empleados:    Lista de empleados para el filtro de responsable (solo jefe).

    Returns:
        Response: Renderizado de `lista_pedidos.html`.
    """
    # Leer todos los parámetros de filtro y orden del query string
    busqueda = request.args.get("busqueda", "")
    estado = request.args.get("estado", "")
    responsable = request.args.get("responsable", "")
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")
    orden_id = request.args.get("orden_id", "")
    orden_fecha = request.args.get("orden_fecha", "")
    rol = session.get("rol")
    user_id = session.get("user_id")

    pedidos, empleados = PedidoService.get_filtered(
        rol, user_id, busqueda, estado, responsable,
        fecha_inicio, fecha_fin, orden_id, orden_fecha
    )

    return render_template(
        "lista_pedidos.html",
        pedidos=pedidos,
        busqueda=busqueda,
        estado=estado,
        responsable=responsable,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        orden_id=orden_id,
        orden_fecha=orden_fecha,
        empleados=empleados
    )


# ===========================================================================
# CREAR PEDIDO (Solo Jefe)
# ===========================================================================
@pedidos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@role_required("jefe")  # Solo el jefe puede crear pedidos
def crear_pedido():
    """
    Muestra y procesa el formulario de creación de un nuevo pedido.

    Soporta dos modos de cliente:
    - "existente": Se selecciona un cliente ya registrado del dropdown.
    - "nuevo":     Se ingresan los datos del cliente que se crea al vuelo.

    GET /pedidos/crear:
        Obtiene listas de clientes y empleados para los selectores del formulario.

    POST /pedidos/crear:
        Procesa el formulario, crea el pedido (y el cliente si es nuevo),
        y redirige a la lista de pedidos.

    Campos del formulario esperados (POST):
        - tipo_cliente:      "existente" o "nuevo".
        - cliente_existente: ID del cliente (si tipo="existente").
        - nombre, telefono, correo: Datos del nuevo cliente (si tipo="nuevo").
        - descripcion:       Descripción del trabajo.
        - fecha_entrega:     Fecha límite 'YYYY-MM-DD'.
        - valor_total:       Precio total pactado.
        - anticipo:          Monto adelantado por el cliente.
        - responsable_id:    ID del empleado responsable del pedido.

    Returns:
        Response: Formulario (GET) o redirección a lista (POST).
    """
    # Obtener datos para los selectores del formulario
    clientes, empleados = PedidoService.get_create_data()

    if request.method == "POST":
        # Leer todos los campos del formulario
        tipo_cliente = request.form["tipo_cliente"]
        cliente_existente = request.form.get("cliente_existente")
        nombre = request.form.get("nombre")
        telefono = request.form.get("telefono")
        correo = request.form.get("correo")
        descripcion = request.form["descripcion"]
        fecha_entrega = request.form["fecha_entrega"]
        valor_total = request.form["valor_total"]
        anticipo = request.form["anticipo"]
        responsable_id = request.form["responsable_id"]

        PedidoService.create_pedido(
            tipo_cliente, cliente_existente, nombre, telefono, correo,
            descripcion, fecha_entrega, valor_total, anticipo, responsable_id
        )
        return redirect(url_for("pedidos.listar_pedidos"))

    return render_template("crear_pedidos.html", clientes=clientes, empleados=empleados)


# ===========================================================================
# ACTUALIZAR ESTADO DE PEDIDO
# ===========================================================================
@pedidos_bp.route("/actualizar_estado/<int:pedido_id>", methods=["POST"])
@login_required
def actualizar_estado(pedido_id):
    """
    Cambia el estado de un pedido existente.

    Accesible para jefe y empleados. El servicio aplica las reglas de negocio:
    - El pedido debe existir.
    - Un pedido "terminado" no puede cambiar de estado.
    - Un empleado solo puede cambiar el estado de sus propios pedidos.

    Si el servicio retorna un error, `abort(status_code)` genera la respuesta
    HTTP apropiada (403 o 400 o 404).

    Args:
        pedido_id (int): ID del pedido cuyo estado se actualiza.

    Campos del formulario esperados:
        - estado (str): El nuevo estado del pedido.

    Returns:
        Response: Redirección a `pedidos.listar_pedidos` (éxito) o
                  error HTTP (fallo).
    """
    nuevo_estado = request.form["estado"]
    rol = session.get("rol")
    user_id = session.get("user_id")

    success, msg, status_code = PedidoService.actualizar_estado(
        pedido_id, nuevo_estado, rol, user_id
    )
    if not success:
        # Lanzar el error HTTP apropiado según el código retornado por el servicio
        abort(status_code)

    return redirect(url_for("pedidos.listar_pedidos"))


# ===========================================================================
# DETALLE DE PEDIDO
# ===========================================================================
@pedidos_bp.route("/<int:pedido_id>")
@login_required
def detalle_pedido(pedido_id):
    """
    Muestra la vista de detalle completo de un pedido.

    Incluye la información del pedido, datos del cliente, datos del responsable,
    y la lista de materiales usados en la producción del pedido.

    Control de acceso por rol:
    - El jefe puede ver cualquier pedido.
    - El empleado solo puede ver sus propios pedidos (responsable_id == user_id).
      Si intenta ver uno ajeno, recibe un error 403.

    Args:
        pedido_id (int): ID del pedido a mostrar.

    Variables enviadas a la plantilla:
        - pedido     (dict): Datos completos del pedido con info del cliente y responsable.
        - produccion (list): Materiales usados en la producción de este pedido.

    Returns:
        Response: Renderizado de `detalle_pedido.html` o error HTTP (403/404).
    """
    rol = session.get("rol")
    user_id = session.get("user_id")

    success, pedido, produccion, status_code = PedidoService.get_detail(
        pedido_id, rol, user_id
    )
    if not success:
        abort(status_code)

    return render_template(
        "detalle_pedido.html",
        pedido=pedido,
        produccion=produccion
    )


# ===========================================================================
# EDITAR PEDIDO (Solo Jefe)
# ===========================================================================
@pedidos_bp.route("/editar/<int:pedido_id>", methods=["GET", "POST"])
@login_required
@role_required("jefe")
def editar_pedido(pedido_id):
    """
    Muestra y procesa el formulario de edición de un pedido.

    Solo el jefe puede editar pedidos, y solo si NO están en estado "terminado".
    Un pedido terminado es inmutable (el servicio retorna código 400 en ese caso).

    GET /pedidos/editar/<id>:
        Obtiene los datos actuales del pedido y los listas de clientes/empleados
        para pre-poblar el formulario.

    POST /pedidos/editar/<id>:
        Actualiza los datos del pedido y redirige a su página de detalle.

    Args:
        pedido_id (int): ID del pedido a editar.

    Returns:
        Response: Formulario pre-poblado (GET), redirección al detalle (POST),
                  o error HTTP (404 si no existe, 400 si está terminado).
    """
    # Obtener datos del pedido y listas para el formulario (con validaciones)
    success, pedido, clientes, empleados, status_code = PedidoService.get_edit_data(pedido_id)
    if not success:
        abort(status_code)

    if request.method == "POST":
        # Extraer todos los campos del formulario de edición
        cliente_id = request.form["cliente_id"]
        descripcion = request.form["descripcion"]
        fecha_entrega = request.form["fecha_entrega"]
        valor_total = request.form["valor_total"]
        anticipo = request.form["anticipo"]
        responsable_id = request.form["responsable_id"]

        PedidoService.update_pedido(
            pedido_id, cliente_id, descripcion, fecha_entrega,
            valor_total, anticipo, responsable_id
        )
        # Redirigir al detalle del pedido editado para confirmar los cambios
        return redirect(url_for("pedidos.detalle_pedido", pedido_id=pedido_id))

    return render_template(
        "editar_pedido.html",
        pedido=pedido,
        clientes=clientes,
        empleados=empleados
    )


# ===========================================================================
# ELIMINAR PEDIDO (Solo Jefe)
# ===========================================================================
@pedidos_bp.route("/eliminar/<int:pedido_id>", methods=["POST"])
@login_required
@role_required("jefe")
def eliminar_pedido(pedido_id):
    """
    Elimina permanentemente un pedido del sistema.

    Solo acepta POST para prevenir eliminaciones accidentales.
    Solo accesible para el jefe (protegido con `@role_required`).
    No tiene confirmación adicional: la UI debe implementar un modal de
    confirmación antes de enviar el formulario POST.

    Args:
        pedido_id (int): ID del pedido a eliminar.

    Returns:
        Response: Redirección a `pedidos.listar_pedidos`.
    """
    PedidoService.delete_pedido(pedido_id)
    return redirect(url_for("pedidos.listar_pedidos"))
