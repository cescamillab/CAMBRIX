from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from functools import wraps
from app.utils import login_required
from app.db import get_connection


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

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Obtener filtros desde la URL
    busqueda = request.args.get("busqueda", "")
    estado = request.args.get("estado", "")
    responsable = request.args.get("responsable","")

    # Query base
    query = """
        SELECT pedidos.*, clientes.nombre AS cliente_nombre,
        usuarios.nombre AS responsable_nombre,
        (pedidos.valor_total - pedidos.anticipo) AS saldo
        FROM pedidos
        JOIN clientes ON pedidos.cliente_id = clientes.id
        LEFT JOIN usuarios ON pedidos.responsable_id = usuarios.id
        WHERE 1=1
    """

    params = []

    # Si no es jefe, solo ve sus pedidos
    if session.get("rol") != "jefe":
        query += " AND pedidos.responsable_id = %s"
        params.append(session.get("user_id"))

    # Filtro por búsqueda de cliente
    if busqueda:
        query += " AND clientes.nombre LIKE %s"
        params.append(f"%{busqueda}%")

    # Filtro por estado
    if estado:
        query += " AND pedidos.estado = %s"
        params.append(estado)

    # Filtro por responsable (solo jefe puede usarlo)
    if responsable and session.get("rol") == "jefe":
        query += " AND pedidos.responsable_id = %s"
        params.append(responsable)

    query += " ORDER BY pedidos.fecha_creacion DESC"

    cursor.execute(query, params)
    pedidos = cursor.fetchall()

    # Obtener lista de empleados para el filtro
    empleados = []
    if session.get("rol") == "jefe":
        cursor.execute("SELECT id, nombre FROM usuarios WHERE rol = 'empleado'")
        empleados = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "lista_pedidos.html",
        pedidos=pedidos,
        busqueda=busqueda,
        estado=estado,
        responsable=responsable,
        empleados=empleados
    )


# CREAR PEDIDO (solo jefe)
@pedidos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@role_required("jefe")

def crear_pedido():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Traer clientes existentes
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    if request.method == "POST":

        tipo_cliente = request.form["tipo_cliente"]

        # Si selecciona cliente existente
        if tipo_cliente == "existente":
            cliente_id = request.form["cliente_existente"]

        # Si crea cliente nuevo
        else:
            nombre = request.form["nombre"]
            telefono = request.form["telefono"]
            correo = request.form["correo"]

            cursor.execute(
                "INSERT INTO clientes (nombre, telefono, correo) VALUES (%s, %s, %s)",
                (nombre, telefono, correo)
            )
            connection.commit()

            cliente_id = cursor.lastrowid

        descripcion = request.form["descripcion"]
        fecha_entrega = request.form["fecha_entrega"]
        valor_total = request.form["valor_total"]
        anticipo = request.form["anticipo"]
        responsable_id = request.form["responsable_id"]


        cursor.execute("""
            INSERT INTO pedidos 
            (cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("pedidos.listar_pedidos"))

    # Traer empleados
    cursor.execute("SELECT id, username FROM usuarios WHERE rol = 'empleado'")
    empleados = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("crear_pedidos.html", clientes=clientes, empleados=empleados)

@pedidos_bp.route("/actualizar_estado/<int:pedido_id>", methods=["POST"])
@login_required
def actualizar_estado(pedido_id):

    nuevo_estado = request.form["estado"]

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Verificar que el pedido existe
    cursor.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
    pedido = cursor.fetchone()

    if not pedido:
        cursor.close()
        connection.close()
        abort(404)

    # Si ya está terminado → bloquear
    if pedido["estado"] == "terminado":
        cursor.close()
        connection.close()
        abort(400)

    # Si es empleado, solo puede cambiar los suyos
    if session.get("rol") == "empleado":
        if pedido["responsable_id"] != session.get("user_id"):
            cursor.close()
            connection.close()
            abort(403)

    # Actualizar estado
    cursor.execute(
        "UPDATE pedidos SET estado = %s WHERE id = %s",
        (nuevo_estado, pedido_id)
    )
    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("pedidos.listar_pedidos"))



@pedidos_bp.route("/<int:pedido_id>")
@login_required
def detalle_pedido(pedido_id):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            pedidos.*, 
            clientes.nombre AS cliente_nombre,
            clientes.telefono,
            clientes.correo,
            usuarios.username AS responsable_nombre,
            (pedidos.valor_total - pedidos.anticipo) AS saldo
        FROM pedidos
        JOIN clientes ON pedidos.cliente_id = clientes.id
        LEFT JOIN usuarios ON pedidos.responsable_id = usuarios.id
        WHERE pedidos.id = %s
    """, (pedido_id,))

    pedido = cursor.fetchone()

    if not pedido:
        cursor.close()
        connection.close()
        abort(404)

    # Si es empleado, solo puede ver los suyos
    if session.get("rol") == "empleado":
        if pedido["responsable_id"] != session.get("user_id"):
            cursor.close()
            connection.close()
            abort(403)

    cursor.close()
    connection.close()

    return render_template("detalle_pedido.html", pedido=pedido)


@pedidos_bp.route("/editar/<int:pedido_id>", methods=["GET", "POST"])
@login_required
@role_required("jefe")
def editar_pedido(pedido_id):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Traer pedido
    cursor.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
    pedido = cursor.fetchone()

    if not pedido:
        cursor.close()
        connection.close()
        abort(404)

    # No permitir editar si está terminado
    if pedido["estado"] == "terminado":
        cursor.close()
        connection.close()
        abort(400)

    # Traer clientes
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    # Traer empleados
    cursor.execute("SELECT id, username FROM usuarios WHERE rol = 'empleado'")
    empleados = cursor.fetchall()

    if request.method == "POST":

        cliente_id = request.form["cliente_id"]
        descripcion = request.form["descripcion"]
        fecha_entrega = request.form["fecha_entrega"]
        valor_total = request.form["valor_total"]
        anticipo = request.form["anticipo"]
        responsable_id = request.form["responsable_id"]

        cursor.execute("""
            UPDATE pedidos
            SET cliente_id=%s,
                descripcion=%s,
                fecha_entrega=%s,
                valor_total=%s,
                anticipo=%s,
                responsable_id=%s
            WHERE id=%s
        """, (
            cliente_id,
            descripcion,
            fecha_entrega,
            valor_total,
            anticipo,
            responsable_id,
            pedido_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("pedidos.detalle_pedido", pedido_id=pedido_id))

    cursor.close()
    connection.close()

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

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("pedidos.listar_pedidos"))
