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

    rol = session.get("rol")

    # =========================
    # ALERTAS DE INVENTARIO
    # =========================

    cursor.execute("""
        SELECT nombre, stock_actual, stock_minimo
        FROM materiales
        WHERE stock_actual <= stock_minimo
        ORDER BY stock_actual ASC
    """)

    materiales_bajos = cursor.fetchall()

    # =========================
    # MÉTRICAS
    # =========================

    if rol == "jefe":

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

        cursor.execute("""
            SELECT estado, COUNT(*) as total
            FROM pedidos
            GROUP BY estado
        """)
        estados = cursor.fetchall()

        cursor.execute("""
            SELECT DATE_FORMAT(fecha_creacion, '%Y-%m') as mes,
                   SUM(valor_total) as total_mes
            FROM pedidos
            GROUP BY mes
            ORDER BY mes
        """)
        ingresos = cursor.fetchall()

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

        cursor.execute("""
            SELECT estado, COUNT(*) as total
            FROM pedidos
            WHERE responsable_id = %s
            GROUP BY estado
        """, (user_id,))
        estados = cursor.fetchall()

        cursor.execute("""
            SELECT DATE_FORMAT(fecha_creacion, '%Y-%m') as mes,
                   SUM(valor_total) as total_mes
            FROM pedidos
            WHERE responsable_id = %s
            GROUP BY mes
            ORDER BY mes
        """, (user_id,))
        ingresos = cursor.fetchall()

    # =========================
    # NUEVOS COMPONENTES DASHBOARD
    # =========================

    if rol == "jefe":
        # Top 5 Materiales
        cursor.execute("""
            SELECT m.nombre, SUM(pm.cantidad_usada) as total_usado
            FROM produccion_materiales pm
            JOIN materiales m ON pm.material_id = m.id
            GROUP BY pm.material_id
            ORDER BY total_usado DESC
            LIMIT 5
        """)
        top_materiales = cursor.fetchall()

        # Top 5 Clientes
        cursor.execute("""
            SELECT c.nombre, SUM(p.valor_total) as total_facturado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            GROUP BY p.cliente_id
            ORDER BY total_facturado DESC
            LIMIT 5
        """)
        top_clientes = cursor.fetchall()

        # Últimos 5 pedidos
        cursor.execute("""
            SELECT p.id, c.nombre as cliente, p.valor_total, p.estado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.fecha_creacion DESC
            LIMIT 5
        """)
        ultimos_pedidos = cursor.fetchall()

    else:
        # Si no es jefe, mostramos listas vacías o adaptadas al empleado
        top_materiales = []
        top_clientes = []
        
        cursor.execute("""
            SELECT p.id, c.nombre as cliente, p.valor_total, p.estado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.responsable_id = %s
            ORDER BY p.fecha_creacion DESC
            LIMIT 5
        """, (user_id,))
        ultimos_pedidos = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        total=total,
        pendientes=pendientes,
        en_proceso=en_proceso,
        terminados=terminados,
        total_facturado=total_facturado,
        total_pendiente=total_pendiente,
        rol=rol,
        estados=estados,
        ingresos=ingresos,
        materiales_bajos=materiales_bajos,
        top_materiales=top_materiales,
        top_clientes=top_clientes,
        ultimos_pedidos=ultimos_pedidos
    )