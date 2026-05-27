from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.produccion_repository import ProduccionRepository
from app.infrastructure.repositories.reporte_repository import ReporteRepository
from io import BytesIO
import os
from flask import current_app
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

class ReporteService:
    @staticmethod
    def get_summary():
        total_pedidos = PedidoRepository.count_total()
        total_materiales = MaterialRepository.get_total_count()
        return total_pedidos, total_materiales

    # ==========================
    # DATOS PARA DATATABLES (JSON)
    # ==========================
    @staticmethod
    def get_datos_pedidos(fecha_inicio, fecha_fin, estado):
        datos = ReporteRepository.get_datos_pedidos(fecha_inicio, fecha_fin, estado)
        
        # Formatear fechas para JSON
        for d in datos:
            d['fecha_creacion'] = str(d['fecha_creacion']) if d['fecha_creacion'] else ''
            d['fecha_entrega'] = str(d['fecha_entrega']) if d['fecha_entrega'] else ''
        return datos

    @staticmethod
    def get_datos_produccion(fecha_inicio, fecha_fin):
        datos = ReporteRepository.get_datos_produccion(fecha_inicio, fecha_fin)
        
        for d in datos:
            d['fecha_inicio'] = str(d['fecha_inicio']) if d['fecha_inicio'] else ''
            d['fecha_fin_real'] = str(d['fecha_fin_real']) if d['fecha_fin_real'] else ''
        return datos

    @staticmethod
    def get_datos_inventario():
        return ReporteRepository.get_datos_inventario()

    @staticmethod
    def get_datos_rentabilidad(fecha_inicio, fecha_fin):
        datos = ReporteRepository.get_datos_rentabilidad(fecha_inicio, fecha_fin)
        
        for d in datos:
            d['fecha_creacion'] = str(d['fecha_creacion']) if d['fecha_creacion'] else ''
            ingreso = float(d['ingreso_neto'])
            if ingreso > 0:
                d['margen_porcentaje'] = round((float(d['margen_bruto']) / ingreso) * 100, 2)
            else:
                d['margen_porcentaje'] = 0
                
        return datos

    @staticmethod
    def get_datos_trazabilidad(fecha_inicio, fecha_fin):
        datos = ReporteRepository.get_datos_trazabilidad(fecha_inicio, fecha_fin)
        
        for d in datos:
            d['fecha_hora'] = str(d['fecha_hora']) if d['fecha_hora'] else ''
        return datos

    # ==========================
    # EXPORTACIONES EXCEL Y PDF
    # ==========================

    @staticmethod
    def generate_excel_rentabilidad(fecha_inicio, fecha_fin):
        datos = ReporteService.get_datos_rentabilidad(fecha_inicio, fecha_fin)
        import pandas as pd
        from io import BytesIO
        df = pd.DataFrame(datos)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Rentabilidad")
        output.seek(0)
        return output

    @staticmethod
    def generate_excel_pedidos(fecha_inicio, fecha_fin):
        df = PedidoRepository.get_pedidos_report_excel(fecha_inicio, fecha_fin)
        import pandas as pd
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Pedidos")
        output.seek(0)
        return output

    @staticmethod
    def generate_pdf_pedidos(fecha_inicio, fecha_fin):
        pedidos = PedidoRepository.get_pedidos_report_pdf(fecha_inicio, fecha_fin)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = ReporteService._add_pdf_header([], "Reporte de Pedidos")
        
        data = [["ID", "Cliente", "Estado", "Fecha", "Valor ($)"]]
        for p in pedidos:
            data.append([
                p.get("id",""),
                str(p.get("cliente",""))[:20],
                p.get("estado","").upper(),
                str(p.get("fecha_creacion",""))[:10],
                f"${p.get('valor_total',0):,.2f}"
            ])
            
        elements.append(ReporteService._build_pdf_table(data))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_excel_produccion(fecha_inicio, fecha_fin):
        df = ProduccionRepository.get_produccion_report_excel(fecha_inicio, fecha_fin)
        import pandas as pd
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Produccion")
        output.seek(0)
        return output

    @staticmethod
    def generate_pdf_produccion(fecha_inicio, fecha_fin):
        registros = ProduccionRepository.get_produccion_report_pdf(fecha_inicio, fecha_fin)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = ReporteService._add_pdf_header([], "Reporte de Producción (Materiales Usados)")
        
        data = [["Pedido", "Fecha", "Material", "Cantidad", "Costo Total ($)"]]
        for r in registros:
            data.append([
                f"#{r.get('pedido_id','')}",
                str(r.get("fecha_creacion",""))[:10],
                str(r.get("material",""))[:25],
                str(r.get("cantidad_usada","")),
                f"${r.get('costo_total',0):,.2f}"
            ])
            
        elements.append(ReporteService._build_pdf_table(data))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_excel_inventario():
        df = MaterialRepository.get_inventory_report()
        import pandas as pd
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventario")
        output.seek(0)
        return output

    @staticmethod
    def generate_pdf_inventario():
        materiales = MaterialRepository.get_inventory_list_for_pdf()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = ReporteService._add_pdf_header([], "Estado Actual de Inventario")
        
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
            
        elements.append(ReporteService._build_pdf_table(data))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # Helpers
    @staticmethod
    def _add_pdf_header(elements, title_text):
        styles = getSampleStyleSheet()
        logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=120, height=60)
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 10))
            except Exception:
                pass
                
        titulo = Paragraph(f"<b>CAMBRIX</b> - {title_text}", styles["Title"])
        fecha = Paragraph(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"])
        elements.append(titulo)
        elements.append(fecha)
        elements.append(Spacer(1, 20))
        return elements

    @staticmethod
    def _build_pdf_table(data, col_widths=None):
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
