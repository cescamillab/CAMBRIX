from flask import Blueprint, render_template, send_file, request, jsonify, session, abort
from app.core.security import login_required
from app.application.services.reporte_service import ReporteService

reportes_bp = Blueprint(
    "reportes",
    __name__,
    url_prefix="/reportes",
    template_folder="templates"
)

# ==========================================
# 1. REPORTES DE VENTAS Y PEDIDOS
# ==========================================
@reportes_bp.route("/pedidos")
@login_required
def pedidos_view():
    return render_template("reportes/pedidos.html")

@reportes_bp.route("/api/pedidos")
@login_required
def api_pedidos():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    estado = request.args.get("estado")
    # Obtener datos usando el servicio
    datos = ReporteService.get_datos_pedidos(fecha_inicio, fecha_fin, estado)
    return jsonify({"data": datos})

@reportes_bp.route("/pedidos/excel")
@login_required
def reporte_pedidos_excel():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    output = ReporteService.generate_excel_pedidos(fecha_inicio, fecha_fin)
    return send_file(output, download_name="reporte_pedidos.xlsx", as_attachment=True)

@reportes_bp.route("/pedidos/pdf")
@login_required
def reporte_pedidos_pdf():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    output = ReporteService.generate_pdf_pedidos(fecha_inicio, fecha_fin)
    return send_file(output, download_name="reporte_pedidos.pdf", as_attachment=True)


# ==========================================
# 2. REPORTES DE PRODUCCIÓN Y EFICIENCIA
# ==========================================
@reportes_bp.route("/produccion")
@login_required
def produccion_view():
    return render_template("reportes/produccion.html")

@reportes_bp.route("/api/produccion")
@login_required
def api_produccion():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    datos = ReporteService.get_datos_produccion(fecha_inicio, fecha_fin)
    return jsonify({"data": datos})

@reportes_bp.route("/produccion/excel")
@login_required
def reporte_produccion_excel():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    output = ReporteService.generate_excel_produccion(fecha_inicio, fecha_fin)
    return send_file(output, download_name="reporte_produccion.xlsx", as_attachment=True)

@reportes_bp.route("/produccion/pdf")
@login_required
def reporte_produccion_pdf():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    output = ReporteService.generate_pdf_produccion(fecha_inicio, fecha_fin)
    return send_file(output, download_name="reporte_produccion.pdf", as_attachment=True)


# ==========================================
# 3. REPORTES DE ROTACIÓN DE INVENTARIO
# ==========================================
@reportes_bp.route("/inventario")
@login_required
def inventario_view():
    return render_template("reportes/inventario.html")

@reportes_bp.route("/api/inventario")
@login_required
def api_inventario():
    datos = ReporteService.get_datos_inventario()
    return jsonify({"data": datos})

@reportes_bp.route("/inventario/excel")
@login_required
def reporte_inventario_excel():
    output = ReporteService.generate_excel_inventario()
    return send_file(output, download_name="reporte_inventario.xlsx", as_attachment=True)

@reportes_bp.route("/inventario/pdf")
@login_required
def reporte_inventario_pdf():
    output = ReporteService.generate_pdf_inventario()
    return send_file(output, download_name="reporte_inventario.pdf", as_attachment=True)


# ==========================================
# 4. REPORTES FINANCIEROS (RENTABILIDAD)
# ==========================================
@reportes_bp.route("/rentabilidad")
@login_required
def rentabilidad_view():
    if session.get("rol") != "jefe":
        abort(403)
    return render_template("reportes/rentabilidad.html")

@reportes_bp.route("/api/rentabilidad")
@login_required
def api_rentabilidad():
    if session.get("rol") != "jefe":
        return jsonify({"data": []}), 403
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    datos = ReporteService.get_datos_rentabilidad(fecha_inicio, fecha_fin)
    return jsonify({"data": datos})

@reportes_bp.route("/rentabilidad/excel")
@login_required
def reporte_rentabilidad_excel():
    if session.get("rol") != "jefe":
        abort(403)
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    output = ReporteService.generate_excel_rentabilidad(fecha_inicio, fecha_fin)
    return send_file(output, download_name="reporte_rentabilidad.xlsx", as_attachment=True)


# ==========================================
# 5. TRAZABILIDAD (AUDITORÍA)
# ==========================================
@reportes_bp.route("/trazabilidad")
@login_required
def trazabilidad_view():
    if session.get("rol") != "jefe":
        abort(403)
    return render_template("reportes/trazabilidad.html")

@reportes_bp.route("/api/trazabilidad")
@login_required
def api_trazabilidad():
    if session.get("rol") != "jefe":
        return jsonify({"data": []}), 403
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    datos = ReporteService.get_datos_trazabilidad(fecha_inicio, fecha_fin)
    return jsonify({"data": datos})