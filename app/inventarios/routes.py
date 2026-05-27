from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.utils import login_required
from app.services.inventario_service import InventarioService

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
    stock_status = request.args.get('stock_status', '')
    categoria = request.args.get('categoria', '')
    
    materiales, alerta_stock, categorias = InventarioService.get_material_list(stock_status, categoria)
    return render_template(
        "lista_materiales.html",
        materiales=materiales,
        alerta_stock=alerta_stock,
        categorias=categorias,
        stock_status=stock_status,
        categoria_seleccionada=categoria
    )

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

        InventarioService.create_material(nombre, categoria, unidad, stock, stock_minimo, costo)
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

    material = InventarioService.get_material(id)

    if request.method == "POST":
        nombre = request.form["nombre"]
        categoria = request.form["categoria"]
        unidad = request.form["unidad"]
        stock_minimo = request.form["stock_minimo"]
        costo = request.form["costo"]

        InventarioService.update_material(id, nombre, categoria, unidad, stock_minimo, costo)
        return redirect(url_for("inventarios.listar_materiales"))

    return render_template("editar_material.html", material=material)


# =========================
# ELIMINAR MATERIAL (SOLO JEFE)
# =========================
@inventarios_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_material(id):
    if session.get("rol") != "jefe":
        return "Acceso no autorizado"

    success, msg = InventarioService.delete_material(id)
    flash(msg, "success" if success else "danger")

    return redirect(url_for("inventarios.listar_materiales"))


# =========================
# REGISTRAR MOVIMIENTO 
# =========================
@inventarios_bp.route("/movimiento/<int:material_id>", methods=["GET", "POST"])
@login_required
def registrar_movimiento(material_id):
    material = InventarioService.get_material(material_id)

    if request.method == "POST":
        tipo = request.form["tipo"]
        cantidad = float(request.form["cantidad"])
        motivo = request.form["motivo"]

        success, msg = InventarioService.registrar_movimiento(material_id, tipo, cantidad, motivo)
        if not success:
            return msg

        return redirect(url_for("inventarios.listar_materiales"))

    return render_template("registrar_movimiento.html", material=material)


# =========================
# HISTORIAL MATERIAL
# =========================
@inventarios_bp.route("/historial/<int:material_id>")
@login_required
def historial_material(material_id):
    material, movimientos = InventarioService.get_historial(material_id)

    return render_template(
        "historial_material.html",
        material=material,
        movimientos=movimientos
    )