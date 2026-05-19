import os
from flask import Blueprint, render_template, send_file, request, current_app
from app.db import get_connection
from app.utils import login_required

import pandas as pd
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from datetime import datetime

reportes_bp = Blueprint(
    "reportes",
    __name__,
    url_prefix="/reportes",
    template_folder="templates"
)

# -------------------------
# HELPERS
# -------------------------
def build_date_query(query_base, date_col, where_started=False):
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    params = []
    
    if fecha_inicio:
        connector = "AND" if where_started else "WHERE"
        query_base += f" {connector} {date_col} >= %s "
        params.append(fecha_inicio + " 00:00:00")
        where_started = True
        
    if fecha_fin:
        connector = "AND" if where_started else "WHERE"
        query_base += f" {connector} {date_col} <= %s "
        params.append(fecha_fin + " 23:59:59")
        
    return query_base, tuple(params)

def add_pdf_header(elements, title_text):
    styles = getSampleStyleSheet()
    
    # Intentar cargar logo si existe
    logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=120, height=60)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 10))
        except Exception:
            pass # Si falla cargando el logo, ignoramos
            
    titulo = Paragraph(f"<b>CAMBRIX</b> - {title_text}", styles["Title"])
    fecha = Paragraph(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"])
    
    elements.append(titulo)
    elements.append(fecha)
    elements.append(Spacer(1, 20))
    return elements

def build_pdf_table(data, col_widths=None):
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#029EF2")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fe")]),
    ]))
    return table

# -------------------------
# PAGINA PRINCIPAL REPORTES
# -------------------------

@reportes_bp.route("/")
@login_required
def ver_reportes():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    # Resúmenes para mostrar en pantalla
    cursor.execute("SELECT COUNT(*) as total FROM pedidos")
    total_pedidos = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as total FROM materiales")
    total_materiales = cursor.fetchone()["total"]
    
    cursor.close()
    conexion.close()
    
    return render_template("reportes.html", total_pedidos=total_pedidos, total_materiales=total_materiales)


# -------------------------
# REPORTES DE PEDIDOS
# -------------------------

@reportes_bp.route("/pedidos/excel")
@login_required
def reporte_pedidos_excel():
    conexion = get_connection()
    query, params = build_date_query("SELECT * FROM pedidos", "fecha_creacion")
    
    df = pd.read_sql(query, conexion, params=params)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pedidos")
        
    output.seek(0)
    conexion.close()
    return send_file(output, download_name="reporte_pedidos.xlsx", as_attachment=True)


@reportes_bp.route("/pedidos/pdf")
@login_required
def reporte_pedidos_pdf():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    base_query = """
        SELECT pedidos.id, clientes.nombre AS cliente, pedidos.estado, pedidos.fecha_creacion, pedidos.valor_total
        FROM pedidos
        JOIN clientes ON pedidos.cliente_id = clientes.id
    """
    query, params = build_date_query(base_query, "pedidos.fecha_creacion")
    
    cursor.execute(query, params)
    pedidos = cursor.fetchall()
    conexion.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = add_pdf_header([], "Reporte de Pedidos")

    data = [["ID", "Cliente", "Estado", "Fecha", "Valor ($)"]]
    for p in pedidos:
        data.append([
            p.get("id",""),
            str(p.get("cliente",""))[:20],
            p.get("estado","").upper(),
            str(p.get("fecha_creacion",""))[:10],
            f"${p.get('valor_total',0):,.2f}"
        ])

    elements.append(build_pdf_table(data))
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, download_name="reporte_pedidos.pdf", as_attachment=True)


# -------------------------
# REPORTES DE PRODUCCION
# -------------------------

@reportes_bp.route("/produccion/excel")
@login_required
def reporte_produccion_excel():
    conexion = get_connection()
    
    base_query = """
    SELECT pm.id, pm.pedido_id, m.nombre AS material, pm.cantidad_usada, pm.costo_unitario, pm.costo_total, p.fecha_creacion
    FROM produccion_materiales pm
    JOIN materiales m ON pm.material_id = m.id
    JOIN pedidos p ON pm.pedido_id = p.id
    """
    query, params = build_date_query(base_query, "p.fecha_creacion")
    
    df = pd.read_sql(query, conexion, params=params)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Produccion")
        
    output.seek(0)
    conexion.close()
    return send_file(output, download_name="reporte_produccion.xlsx", as_attachment=True)


@reportes_bp.route("/produccion/pdf")
@login_required
def reporte_produccion_pdf():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    base_query = """
    SELECT pm.pedido_id, m.nombre AS material, pm.cantidad_usada, pm.costo_total, p.fecha_creacion
    FROM produccion_materiales pm
    JOIN materiales m ON pm.material_id = m.id
    JOIN pedidos p ON pm.pedido_id = p.id
    """
    query, params = build_date_query(base_query, "p.fecha_creacion")
    
    cursor.execute(query, params)
    registros = cursor.fetchall()
    conexion.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = add_pdf_header([], "Reporte de Producción (Materiales Usados)")

    data = [["Pedido", "Fecha", "Material", "Cantidad", "Costo Total ($)"]]
    for r in registros:
        data.append([
            f"#{r.get('pedido_id','')}",
            str(r.get("fecha_creacion",""))[:10],
            str(r.get("material",""))[:25],
            str(r.get("cantidad_usada","")),
            f"${r.get('costo_total',0):,.2f}"
        ])

    elements.append(build_pdf_table(data))
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, download_name="reporte_produccion.pdf", as_attachment=True)


# -------------------------
# REPORTES DE INVENTARIO
# -------------------------

@reportes_bp.route("/inventario/excel")
@login_required
def reporte_inventario_excel():
    conexion = get_connection()
    # Inventario no tiene fecha de creación, es el estado actual. No aplicamos filtros de fecha.
    df = pd.read_sql("SELECT id, nombre, stock_actual, stock_minimo, precio_compra FROM materiales", conexion)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventario")
        
    output.seek(0)
    conexion.close()
    return send_file(output, download_name="reporte_inventario.xlsx", as_attachment=True)


@reportes_bp.route("/inventario/pdf")
@login_required
def reporte_inventario_pdf():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("SELECT nombre, stock_actual, stock_minimo, precio_compra FROM materiales ORDER BY nombre")
    materiales = cursor.fetchall()
    conexion.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = add_pdf_header([], "Estado Actual de Inventario")

    data = [["Material", "Stock Actual", "Stock Mínimo", "Precio Compra ($)", "Estado"]]
    for m in materiales:
        estado = "OK" if m.get("stock_actual",0) > m.get("stock_minimo",0) else "BAJO STOCK"
        data.append([
            str(m.get("nombre",""))[:30],
            str(m.get("stock_actual","")),
            str(m.get("stock_minimo","")),
            f"${m.get('precio_compra',0):,.2f}",
            estado
        ])

    elements.append(build_pdf_table(data))
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, download_name="reporte_inventario.pdf", as_attachment=True)