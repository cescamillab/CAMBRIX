from flask import Blueprint, render_template, session
from app.utils import login_required

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
    return render_template("dashboard.html", rol=rol)
