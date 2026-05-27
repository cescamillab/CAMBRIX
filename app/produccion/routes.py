from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.utils import login_required
from app.services.produccion_service import ProduccionService

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
    success, pedido, materiales, usados, costo_acumulado = ProduccionService.get_produccion_data(pedido_id)
    if not success:
        return pedido, 404

    if request.method == "POST":
        material_id = request.form["material_id"]
        cantidad = float(request.form["cantidad"])

        success_proc, msg, flash_type = ProduccionService.procesar_material(pedido_id, material_id, cantidad)
        flash(msg, flash_type)
        
        return redirect(url_for("produccion.gestionar_produccion", pedido_id=pedido_id))

    return render_template(
        "gestionar_produccion.html",
        pedido=pedido,
        materiales=materiales,
        usados=usados,
        costo_acumulado=costo_acumulado
    )