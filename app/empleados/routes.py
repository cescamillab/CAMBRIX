from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_connection

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
        
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, username, rol FROM usuarios")
    empleados = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template("listar_empleados.html", empleados=empleados)

@empleados_bp.route("/empleados/crear", methods=["POST"])
def crear_empleado():
    if not es_jefe():
        return redirect(url_for("dashboard.home"))
        
    nombre = request.form.get("nombre")
    username = request.form.get("username")
    password = request.form.get("password")
    rol = request.form.get("rol")
    
    if nombre and username and password and rol:
        try:
            connection = get_connection()
            cursor = connection.cursor()
            query = "INSERT INTO usuarios (nombre, username, password, rol) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (nombre, username, password, rol))
            connection.commit()
            flash("Empleado creado exitosamente.", "success")
        except Exception as e:
            flash(f"Error al crear empleado: {e}", "danger")
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()
            
    return redirect(url_for("empleados.listar_empleados"))

@empleados_bp.route("/empleados/editar/<int:id>", methods=["POST"])
def editar_empleado(id):
    if not es_jefe():
        return redirect(url_for("dashboard.home"))
        
    nombre = request.form.get("nombre")
    username = request.form.get("username")
    password = request.form.get("password")
    rol = request.form.get("rol")
    
    if nombre and username and rol:
        try:
            connection = get_connection()
            cursor = connection.cursor()
            
            if password: # Si se proporciona contraseña, actualizarla
                query = "UPDATE usuarios SET nombre=%s, username=%s, password=%s, rol=%s WHERE id=%s"
                cursor.execute(query, (nombre, username, password, rol, id))
            else:
                query = "UPDATE usuarios SET nombre=%s, username=%s, rol=%s WHERE id=%s"
                cursor.execute(query, (nombre, username, rol, id))
                
            connection.commit()
            flash("Empleado actualizado exitosamente.", "success")
        except Exception as e:
            flash(f"Error al actualizar empleado: {e}", "danger")
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()
            
    return redirect(url_for("empleados.listar_empleados"))

@empleados_bp.route("/empleados/eliminar/<int:id>", methods=["POST"])
def eliminar_empleado(id):
    if not es_jefe():
        return redirect(url_for("dashboard.home"))
        
    # Prevenir que el jefe se elimine a sí mismo
    if id == session.get("user_id"):
        flash("No puedes eliminar tu propia cuenta.", "warning")
        return redirect(url_for("empleados.listar_empleados"))
        
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
        connection.commit()
        flash("Empleado eliminado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar empleado: {e}", "danger")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'connection' in locals(): connection.close()
        
    return redirect(url_for("empleados.listar_empleados"))
