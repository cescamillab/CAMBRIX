from flask import Blueprint, render_template, session
from app.utils import login_required
from app.db import get_connection

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
    template_folder="templates"
)

@dashboard_bp.route("/")
@login_required
def home():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    if session.get("rol") == "jefe":

        cursor.execute("SELECT COUNT(*) AS total FROM pedidos")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS pendientes FROM pedidos WHERE estado = 'pendiente'")
        pendientes = cursor.fetchone()["pendientes"]

        cursor.execute("SELECT COUNT(*) AS en_proceso FROM pedidos WHERE estado = 'en_proceso'")
        en_proceso = cursor.fetchone()["en_proceso"]

        cursor.execute("SELECT COUNT(*) AS terminados FROM pedidos WHERE estado = 'terminado'")
        terminados = cursor.fetchone()["terminados"]

        cursor.execute("SELECT SUM(valor_total) AS total_facturado FROM pedidos")
        total_facturado = cursor.fetchone()["total_facturado"] or 0

        cursor.execute("SELECT SUM(valor_total - anticipo) AS total_pendiente FROM pedidos")
        total_pendiente = cursor.fetchone()["total_pendiente"] or 0

    else:
        user_id = session.get("user_id")

        cursor.execute("SELECT COUNT(*) AS total FROM pedidos WHERE responsable_id = %s", (user_id,))
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS pendientes FROM pedidos WHERE responsable_id = %s AND estado = 'pendiente'", (user_id,))
        pendientes = cursor.fetchone()["pendientes"]

        cursor.execute("SELECT COUNT(*) AS en_proceso FROM pedidos WHERE responsable_id = %s AND estado = 'en_proceso'", (user_id,))
        en_proceso = cursor.fetchone()["en_proceso"]

        cursor.execute("SELECT COUNT(*) AS terminados FROM pedidos WHERE responsable_id = %s AND estado = 'terminado'", (user_id,))
        terminados = cursor.fetchone()["terminados"]

        cursor.execute("SELECT SUM(valor_total) AS total_facturado FROM pedidos WHERE responsable_id = %s", (user_id,))
        total_facturado = cursor.fetchone()["total_facturado"] or 0

        cursor.execute("SELECT SUM(valor_total - anticipo) AS total_pendiente FROM pedidos WHERE responsable_id = %s", (user_id,))
        total_pendiente = cursor.fetchone()["total_pendiente"] or 0

    cursor.close()
    connection.close()
    rol = session.get("rol")

    return render_template(
        "dashboard.html",
        total=total,
        pendientes=pendientes,
        en_proceso=en_proceso,
        terminados=terminados,
        total_facturado=total_facturado,
        total_pendiente=total_pendiente,
        rol=rol
    )