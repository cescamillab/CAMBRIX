from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.empleado_service import EmpleadoService

empleados_bp = Blueprint(
    "empleados",
    __name__,
    template_folder="templates"
)

def es_jefe():
    return session.get("rol") == "jefe"

@empleados_bp.route("/empleados")
def listar_empleados():
    if not es_jefe():
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("dashboard.home"))
        
    empleados = EmpleadoService.get_all_empleados()
    return render_template("listar_empleados.html", empleados=empleados)

@empleados_bp.route("/empleados/crear", methods=["POST"])
def crear_empleado():
    if not es_jefe():
        return redirect(url_for("dashboard.home"))
        
    nombre = request.form.get("nombre")
    username = request.form.get("username")
    password = request.form.get("password")
    rol = request.form.get("rol")
    
    success, msg = EmpleadoService.create_empleado(nombre, username, password, rol)
    flash(msg, "success" if success else "danger")
            
    return redirect(url_for("empleados.listar_empleados"))

@empleados_bp.route("/empleados/editar/<int:id>", methods=["POST"])
def editar_empleado(id):
    if not es_jefe():
        return redirect(url_for("dashboard.home"))
        
    nombre = request.form.get("nombre")
    username = request.form.get("username")
    password = request.form.get("password")
    rol = request.form.get("rol")
    
    success, msg = EmpleadoService.update_empleado(id, nombre, username, rol, password)
    flash(msg, "success" if success else "danger")
            
    return redirect(url_for("empleados.listar_empleados"))

@empleados_bp.route("/empleados/eliminar/<int:id>", methods=["POST"])
def eliminar_empleado(id):
    if not es_jefe():
        return redirect(url_for("dashboard.home"))
        
    success, msg = EmpleadoService.delete_empleado(id, session.get("user_id"))
    flash(msg, "success" if success else ("warning" if "propia" in msg else "danger"))
        
    return redirect(url_for("empleados.listar_empleados"))

