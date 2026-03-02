from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import get_connection
from app.utils import login_required

produccion_bp = Blueprint(
    "produccion",
    __name__,
    url_prefix="/produccion",
    template_folder="templates"
)

from . import routes

@produccion_bp.route("/pedido/<int:pedido_id>", methods=["GET", "POST"])
@login_required
def gestionar_produccion(pedido_id):

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # Obtener pedido
    cursor.execute("SELECT * FROM pedidos WHERE id=%s", (pedido_id,))
    pedido = cursor.fetchone()
    
    if not pedido:
        return "Pedido no encontrado", 404

    # Si está pendiente → cambiar a en_proceso
    if pedido["estado"] == "pendiente":
        cursor.execute(
            "UPDATE pedidos SET estado = 'en_proceso' WHERE id = %s",
            (pedido_id,)
        )
        conexion.commit()

        # Volvemos a consultar para tener estado actualizado
        cursor.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
        pedido = cursor.fetchone()

    # Obtener materiales disponibles
    cursor.execute("SELECT * FROM materiales ORDER BY nombre")
    materiales = cursor.fetchall()

    if request.method == "POST":

        material_id = request.form["material_id"]
        cantidad = float(request.form["cantidad"])

        # Obtener material seleccionado
        cursor.execute("SELECT * FROM materiales WHERE id=%s", (material_id,))
        material = cursor.fetchone()

        if cantidad > float(material["stock_actual"]):
            conexion.close()
            return "Stock insuficiente"

        costo_unitario = float(material["costo_unitario"])
        costo_total = costo_unitario * cantidad

        # Registrar producción
        cursor.execute("""
            INSERT INTO produccion_materiales
            (pedido_id, material_id, cantidad_usada, costo_unitario, costo_total)
            VALUES (%s, %s, %s, %s, %s)
        """, (pedido_id, material_id, cantidad, costo_unitario, costo_total))

        # Registrar movimiento inventario
        cursor.execute("""
            INSERT INTO movimientos_inventario
            (material_id, tipo, cantidad, motivo, pedido_id)
            VALUES (%s, 'salida', %s, %s, %s)
        """, (material_id, cantidad,
              f"Producción Pedido #{pedido_id}", pedido_id))

        # Actualizar stock
        nuevo_stock = float(material["stock_actual"]) - cantidad
        cursor.execute("""
            UPDATE materiales
            SET stock_actual=%s
            WHERE id=%s
        """, (nuevo_stock, material_id))

        conexion.commit()
        conexion.close()

        return redirect(url_for("produccion.gestionar_produccion",
                                pedido_id=pedido_id))

    # Obtener materiales ya usados en el pedido
    cursor.execute("""
        SELECT pm.*, m.nombre
        FROM produccion_materiales pm
        JOIN materiales m ON pm.material_id = m.id
        WHERE pm.pedido_id=%s
    """, (pedido_id,))
    usados = cursor.fetchall()

    conexion.close()

    return render_template(
        "gestionar_produccion.html",
        pedido=pedido,
        materiales=materiales,
        usados=usados
    )