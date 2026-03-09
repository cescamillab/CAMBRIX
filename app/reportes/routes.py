from flask import Blueprint, render_template, send_file
from app.db import get_connection
from app.utils import login_required

import pandas as pd
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from datetime import datetime
from reportlab.pdfgen import canvas


reportes_bp = Blueprint(
    "reportes",
    __name__,
    url_prefix="/reportes",
    template_folder="templates"
)

from . import routes


# -------------------------
# PAGINA PRINCIPAL REPORTES
# -------------------------

@reportes_bp.route("/")
@login_required
def ver_reportes():
    return render_template("reportes.html")


# -------------------------
# REPORTE PEDIDOS EXCEL
# -------------------------

@reportes_bp.route("/pedidos/excel")
@login_required
def reporte_pedidos_excel():

    conexion = get_connection()

    df = pd.read_sql("SELECT * FROM pedidos", conexion)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pedidos")

    output.seek(0)
    conexion.close()

    return send_file(
        output,
        download_name="reporte_pedidos.xlsx",
        as_attachment=True
    )


# -------------------------
# REPORTE PRODUCCION EXCEL
# -------------------------

@reportes_bp.route("/produccion/excel")
@login_required
def reporte_produccion_excel():

    conexion = get_connection()

    query = """
    SELECT pm.id, pm.pedido_id, m.nombre, pm.cantidad_usada,
           pm.costo_unitario, pm.costo_total
    FROM produccion_materiales pm
    JOIN materiales m ON pm.material_id = m.id
    """

    df = pd.read_sql(query, conexion)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Produccion")

    output.seek(0)
    conexion.close()

    return send_file(
        output,
        download_name="reporte_produccion.xlsx",
        as_attachment=True
    )


# -------------------------
# REPORTE INVENTARIO EXCEL
# -------------------------

@reportes_bp.route("/inventario/excel")
@login_required
def reporte_inventario_excel():

    conexion = get_connection()

    df = pd.read_sql("SELECT * FROM materiales", conexion)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventario")

    output.seek(0)
    conexion.close()

    return send_file(
        output,
        download_name="reporte_inventario.xlsx",
        as_attachment=True
    )


# -------------------------
# REPORTE PEDIDOS PDF
# -------------------------

@reportes_bp.route("/pedidos/pdf")
@login_required
def reporte_pedidos_pdf():

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            pedidos.id,
            clientes.nombre AS cliente,
            pedidos.estado,
            pedidos.fecha_creacion,
            pedidos.valor_total
        FROM pedidos
        JOIN clientes ON pedidos.cliente_id = clientes.id
    """)
    pedidos = cursor.fetchall()

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)

    elements = []

    styles = getSampleStyleSheet()

    titulo = Paragraph("Reporte de Pedidos", styles["Title"])
    fecha = Paragraph(
        f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    )

    elements.append(titulo)
    elements.append(fecha)
    elements.append(Spacer(1,20))

    # Cabecera tabla
    data = [["ID", "Cliente", "Estado", "Fecha", "Valor"]]

    for p in pedidos:
        data.append([
            p.get("id",""),
            p.get("cliente",""),
            p.get("estado",""),
            str(p.get("fecha_creacion","")),
            p.get("valor_total",""),
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

        ("BOTTOMPADDING",(0,0),(-1,0),12),

        ("BACKGROUND",(0,1),(-1,-1),colors.beige),

        ("GRID",(0,0),(-1,-1),1,colors.black),

    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    conexion.close()

    return send_file(
        buffer,
        download_name="reporte_pedidos.pdf",
        as_attachment=True
    )