from flask import Blueprint, render_template, request, redirect, url_for, session
from app.utils import login_required
from app.db import get_connection

inventarios_bp = Blueprint(
    "inventarios",
    __name__,
    url_prefix="/inventarios",
    template_folder="templates"
)

# =========================
# LISTAR MATERIALES
# =========================
@inventarios_bp.route("/")
@login_required
def listar_materiales():

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM materiales ORDER BY nombre")
    materiales = cursor.fetchall()

    conexion.close()

    return render_template("lista_materiales.html",
                           materiales=materiales)


# =========================
# CREAR MATERIAL (SOLO JEFE)
# =========================
@inventarios_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear_material():

    if session.get("rol") != "jefe":
        return "Acceso no autorizado"

    if request.method == "POST":

        nombre = request.form["nombre"]
        categoria = request.form["categoria"]
        unidad = request.form["unidad"]
        stock = request.form["stock"]
        stock_minimo = request.form["stock_minimo"]
        costo = request.form["costo"]

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO materiales
            (nombre, categoria, unidad_medida, stock_actual, stock_minimo, costo_unitario)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, categoria, unidad, stock, stock_minimo, costo))

        conexion.commit()
        conexion.close()

        return redirect(url_for("inventarios.listar_materiales"))

    return render_template("crear_material.html")


# =========================
# EDITAR MATERIAL (SOLO JEFE)
# =========================
@inventarios_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_material(id):

    if session.get("rol") != "jefe":
        return "Acceso no autorizado"

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM materiales WHERE id=%s", (id,))
    material = cursor.fetchone()

    if request.method == "POST":

        nombre = request.form["nombre"]
        categoria = request.form["categoria"]
        unidad = request.form["unidad"]
        stock_minimo = request.form["stock_minimo"]
        costo = request.form["costo"]

        cursor.execute("""
            UPDATE materiales
            SET nombre=%s,
                categoria=%s,
                unidad_medida=%s,
                stock_minimo=%s,
                costo_unitario=%s
            WHERE id=%s
        """, (nombre, categoria, unidad, stock, stock_minimo, costo, id))

        conexion.commit()
        conexion.close()

        return redirect(url_for("inventarios.listar_materiales"))

    conexion.close()

    return render_template("editar_material.html",
                           material=material)


# =========================
# ELIMINAR MATERIAL (SOLO JEFE)
# =========================
@inventarios_bp.route("/eliminar/<int:id>")
@login_required
def eliminar_material(id):

    if session.get("rol") != "jefe":
        return "Acceso no autorizado"

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM materiales WHERE id=%s", (id,))
    conexion.commit()
    conexion.close()

    return redirect(url_for("inventarios.listar_materiales"))


# =========================
# REGISTRAR MOVIMIENTO 
# =========================
@inventarios_bp.route("/movimiento/<int:material_id>", methods=["GET", "POST"])
@login_required
def registrar_movimiento(material_id):

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM materiales WHERE id=%s", (material_id,))
    material = cursor.fetchone()

    if request.method == "POST":

        tipo = request.form["tipo"]
        cantidad = float(request.form["cantidad"])
        motivo = request.form["motivo"]

        # Validación básica
        if tipo == "salida" and cantidad > float(material["stock_actual"]):
            conexion.close()
            return "No hay suficiente stock"

        # Insertar movimiento
        cursor.execute("""
            INSERT INTO movimientos_inventario
            (material_id, tipo, cantidad, motivo)
            VALUES (%s, %s, %s, %s)
        """, (material_id, tipo, cantidad, motivo))

        # Actualizar stock
        if tipo == "entrada":
            nuevo_stock = float(material["stock_actual"]) + cantidad
        else:
            nuevo_stock = float(material["stock_actual"]) - cantidad

        cursor.execute("""
            UPDATE materiales
            SET stock_actual=%s
            WHERE id=%s
        """, (nuevo_stock, material_id))

        conexion.commit()
        conexion.close()

        return redirect(url_for("inventarios.listar_materiales"))

    conexion.close()

    return render_template("registrar_movimiento.html",
                           material=material)


# =========================
# HISTORIAL MATERIAL
# =========================
@inventarios_bp.route("/historial/<int:material_id>")
@login_required
def historial_material(material_id):

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # Obtener material
    cursor.execute("SELECT * FROM materiales WHERE id=%s", (material_id,))
    material = cursor.fetchone()

    # Obtener movimientos
    cursor.execute("""
        SELECT m.*, p.id AS pedido_relacionado
        FROM movimientos_inventario m
        LEFT JOIN pedidos p ON m.pedido_id = p.id
        WHERE m.material_id=%s
        ORDER BY m.fecha DESC
    """, (material_id,))

    movimientos = cursor.fetchall()

    conexion.close()

    return render_template(
        "historial_material.html",
        material=material,
        movimientos=movimientos
    )