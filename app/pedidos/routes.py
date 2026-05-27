from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from functools import wraps
from app.utils import login_required
from app.services.pedido_service import PedidoService

pedidos_bp = Blueprint(
    "pedidos",
    __name__,
    url_prefix="/pedidos",
    template_folder="templates"
)

# Decorador para roles
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("rol") != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# LISTAR PEDIDOS
@pedidos_bp.route("/")
@login_required
def listar_pedidos():
    busqueda = request.args.get("busqueda", "")
    estado = request.args.get("estado", "")
    responsable = request.args.get("responsable","")
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")
    orden_id = request.args.get("orden_id", "")
    orden_fecha = request.args.get("orden_fecha", "")
    rol = session.get("rol")
    user_id = session.get("user_id")

    pedidos, empleados = PedidoService.get_filtered(rol, user_id, busqueda, estado, responsable, fecha_inicio, fecha_fin, orden_id, orden_fecha)

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


# CREAR PEDIDO (solo jefe)
@pedidos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@role_required("jefe")
def crear_pedido():
    clientes, empleados = PedidoService.get_create_data()

    if request.method == "POST":
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

        PedidoService.create_pedido(tipo_cliente, cliente_existente, nombre, telefono, correo, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)
        return redirect(url_for("pedidos.listar_pedidos"))

    return render_template("crear_pedidos.html", clientes=clientes, empleados=empleados)

@pedidos_bp.route("/actualizar_estado/<int:pedido_id>", methods=["POST"])
@login_required
def actualizar_estado(pedido_id):
    nuevo_estado = request.form["estado"]
    rol = session.get("rol")
    user_id = session.get("user_id")

    success, msg, status_code = PedidoService.actualizar_estado(pedido_id, nuevo_estado, rol, user_id)
    if not success:
        abort(status_code)

    return redirect(url_for("pedidos.listar_pedidos"))



@pedidos_bp.route("/<int:pedido_id>")
@login_required
def detalle_pedido(pedido_id):
    rol = session.get("rol")
    user_id = session.get("user_id")

    success, pedido, produccion, status_code = PedidoService.get_detail(pedido_id, rol, user_id)
    if not success:
        abort(status_code)

    return render_template(
        "detalle_pedido.html",
        pedido=pedido,
        produccion=produccion
    )

@pedidos_bp.route("/editar/<int:pedido_id>", methods=["GET", "POST"])
@login_required
@role_required("jefe")
def editar_pedido(pedido_id):
    success, pedido, clientes, empleados, status_code = PedidoService.get_edit_data(pedido_id)
    if not success:
        abort(status_code)

    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        descripcion = request.form["descripcion"]
        fecha_entrega = request.form["fecha_entrega"]
        valor_total = request.form["valor_total"]
        anticipo = request.form["anticipo"]
        responsable_id = request.form["responsable_id"]

        PedidoService.update_pedido(pedido_id, cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)
        return redirect(url_for("pedidos.detalle_pedido", pedido_id=pedido_id))

    return render_template(
        "editar_pedido.html",
        pedido=pedido,
        clientes=clientes,
        empleados=empleados
    )

@pedidos_bp.route("/eliminar/<int:pedido_id>", methods=["POST"])
@login_required
@role_required("jefe")
def eliminar_pedido(pedido_id):
    PedidoService.delete_pedido(pedido_id)
    return redirect(url_for("pedidos.listar_pedidos"))

