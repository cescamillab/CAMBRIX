from flask import Blueprint, render_template, session
from app.core.security import login_required
from app.application.services.dashboard_service import DashboardService

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
    template_folder="templates"
)

@dashboard_bp.route("/")
@login_required
def home():
    rol = session.get("rol")
    user_id = session.get("user_id")

    metrics = DashboardService.get_metrics(rol, user_id)

    return render_template(
        "dashboard.html",
        total=metrics["total"],
        pendientes=metrics["pendientes"],
        en_proceso=metrics["en_proceso"],
        terminados=metrics["terminados"],
        total_facturado=metrics["total_facturado"],
        total_pendiente=metrics["total_pendiente"],
        rol=rol,
        estados=metrics["estados"],
        ingresos=metrics["ingresos"],
        materiales_bajos=metrics["materiales_bajos"],
        top_materiales=metrics["top_materiales"],
        top_clientes=metrics["top_clientes"],
        ultimos_pedidos=metrics["ultimos_pedidos"]
    )
