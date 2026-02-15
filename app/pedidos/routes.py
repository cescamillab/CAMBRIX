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

    if session.get("rol") == "jefe":
        cursor.execute("""
            SELECT pedidos.*, clientes.nombre AS cliente_nombre,
            usuarios.nombre AS responsable_nombre
            FROM pedidos
            JOIN clientes ON pedidos.cliente_id = clientes.id
            LEFT JOIN usuarios ON pedidos.responsable_id = usuarios.id
            ORDER BY pedidos.fecha_creacion DESC
        """)
    else:
        cursor.execute("""
            SELECT pedidos.*, clientes.nombre AS cliente_nombre,
            usuarios.nombre AS responsable_nombre
            FROM pedidos
            JOIN clientes ON pedidos.cliente_id = clientes.id
            LEFT JOIN usuarios ON pedidos.responsable_id = usuarios.id
            WHERE pedidos.responsable_id = %s
            ORDER BY pedidos.fecha_creacion DESC
        """, (session.get("user_id"),))

    pedidos = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("lista_pedidos.html", pedidos=pedidos)


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