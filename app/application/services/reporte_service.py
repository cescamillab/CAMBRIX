"""
app/application/services/reporte_service.py - Servicio de Reportes
====================================================================
Responsabilidad: Orquesta la generación de todos los reportes del sistema,
tanto para visualización en pantalla (datos JSON para DataTables) como para
exportación en archivos descargables (Excel .xlsx y PDF).

Tipos de reportes disponibles:
    1. Pedidos:       Listado de ventas/pedidos con filtros de fecha y estado.
    2. Producción:    Detalle de materiales usados en la producción por pedido.
    3. Inventario:    Estado actual del inventario con valuación.
    4. Rentabilidad:  Análisis financiero con margen bruto por pedido (solo jefe).
    5. Trazabilidad:  Log de auditoría de movimientos de inventario (solo jefe).

Flujo de datos según el tipo de consumo:
    A. Para la tabla de datos en pantalla (DataTables):
       Browser → Blueprint (GET /api/...) → Service.get_datos_*() → Repository → JSON

    B. Para exportación Excel:
       Browser → Blueprint (GET /.../excel) → Service.generate_excel_*() → BytesIO → send_file

    C. Para exportación PDF:
       Browser → Blueprint (GET /.../pdf) → Service.generate_pdf_*() → BytesIO → send_file

Bibliotecas utilizadas:
    - pandas + openpyxl: Para generar archivos Excel. `pandas.ExcelWriter` con
      el motor `openpyxl` permite escribir un DataFrame directamente a un .xlsx.
    - reportlab: Para generar PDFs con tablas estilizadas. Se usa el módulo
      `platypus` de reportlab para componer documentos con elementos como
      tablas, párrafos e imágenes.

Patrón BytesIO (Buffer en Memoria):
    Los archivos generados (Excel y PDF) NO se guardan en disco. Se escriben
    en un buffer de memoria (`BytesIO`), que se retorna al Blueprint y luego
    se envía directamente al navegador con `send_file()`. Esto es más eficiente
    y evita gestionar archivos temporales.

    Flujo:
        buffer = BytesIO()          # Crear buffer vacío en memoria
        ...escribir datos en buffer...
        buffer.seek(0)              # Regresar el puntero al inicio del buffer
        return buffer               # El Blueprint llama send_file(buffer, ...)
"""
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
    """
    Servicio de generación de reportes para visualización y exportación.
    """

    @staticmethod
    def get_summary():
        """
        Obtiene el resumen de conteos generales para la página de reportes.

        Usado para mostrar los KPIs de la cabecera de la sección de reportes.

        Returns:
            tuple(int, int): (total_pedidos, total_materiales)
        """
        total_pedidos = PedidoRepository.count_total()
        total_materiales = MaterialRepository.get_total_count()
        return total_pedidos, total_materiales

    # ===========================================================================
    # DATOS PARA VISUALIZACIÓN EN PANTALLA (API JSON para DataTables)
    # ===========================================================================

    @staticmethod
    def get_datos_pedidos(fecha_inicio, fecha_fin, estado):
        """
        Obtiene y formatea los datos de pedidos para el reporte en pantalla.

        Convierte los objetos `date`/`datetime` a strings para que puedan
        ser serializados a JSON por Flask's `jsonify()`. Los objetos de fecha
        de Python no son directamente serializables a JSON.

        Args:
            fecha_inicio (str|None): Fecha inicio del filtro.
            fecha_fin    (str|None): Fecha fin del filtro.
            estado       (str|None): Estado a filtrar.

        Returns:
            list[dict]: Lista de pedidos con fechas convertidas a strings.
        """
        datos = ReporteRepository.get_datos_pedidos(fecha_inicio, fecha_fin, estado)

        # Convertir objetos date/datetime a strings para serialización JSON
        for d in datos:
            d['fecha_creacion'] = str(d['fecha_creacion']) if d['fecha_creacion'] else ''
            d['fecha_entrega'] = str(d['fecha_entrega']) if d['fecha_entrega'] else ''
        return datos

    @staticmethod
    def get_datos_produccion(fecha_inicio, fecha_fin):
        """
        Obtiene y formatea los datos de producción para el reporte en pantalla.

        Args:
            fecha_inicio (str|None): Fecha inicio del filtro.
            fecha_fin    (str|None): Fecha fin del filtro.

        Returns:
            list[dict]: Lista de registros de producción con fechas como strings.
        """
        datos = ReporteRepository.get_datos_produccion(fecha_inicio, fecha_fin)

        # Las fechas vienen como objetos date de MySQL, se convierten a string
        for d in datos:
            d['fecha_inicio'] = str(d['fecha_inicio']) if d['fecha_inicio'] else ''
            d['fecha_fin_real'] = str(d['fecha_fin_real']) if d['fecha_fin_real'] else ''
        return datos

    @staticmethod
    def get_datos_inventario():
        """
        Obtiene los datos del inventario actual (sin filtros de fecha).

        Returns:
            list[dict]: Datos del inventario con valuación calculada.
        """
        return ReporteRepository.get_datos_inventario()

    @staticmethod
    def get_datos_rentabilidad(fecha_inicio, fecha_fin):
        """
        Obtiene y enriquece los datos de rentabilidad para el reporte financiero.

        Además de obtener los datos del repositorio, calcula el `margen_porcentaje`
        como dato adicional en Python (no en SQL) para evitar división por cero
        de forma controlada.

        Fórmula del margen_porcentaje:
            margen_porcentaje = (margen_bruto / ingreso_neto) * 100

        Si ingreso_neto = 0, se asigna 0% de margen para evitar ZeroDivisionError.

        Args:
            fecha_inicio (str|None): Fecha inicio del filtro.
            fecha_fin    (str|None): Fecha fin del filtro.

        Returns:
            list[dict]: Lista de pedidos con análisis financiero, incluyendo el
                        campo adicional `margen_porcentaje` (float, redondeado a 2 decimales).
        """
        datos = ReporteRepository.get_datos_rentabilidad(fecha_inicio, fecha_fin)

        for d in datos:
            d['fecha_creacion'] = str(d['fecha_creacion']) if d['fecha_creacion'] else ''
            ingreso = float(d['ingreso_neto'])
            if ingreso > 0:
                # Calcular el porcentaje de margen sobre el ingreso total
                d['margen_porcentaje'] = round((float(d['margen_bruto']) / ingreso) * 100, 2)
            else:
                # Protección contra división por cero
                d['margen_porcentaje'] = 0

        return datos

    @staticmethod
    def get_datos_trazabilidad(fecha_inicio, fecha_fin):
        """
        Obtiene los datos del log de auditoría de inventario.

        Args:
            fecha_inicio (str|None): Fecha inicio del filtro.
            fecha_fin    (str|None): Fecha fin del filtro.

        Returns:
            list[dict]: Lista de hasta 100 movimientos con fechas como strings.
        """
        datos = ReporteRepository.get_datos_trazabilidad(fecha_inicio, fecha_fin)

        # Convertir timestamps a strings para serialización JSON
        for d in datos:
            d['fecha_hora'] = str(d['fecha_hora']) if d['fecha_hora'] else ''
        return datos

    # ===========================================================================
    # EXPORTACIONES A EXCEL (.xlsx) usando pandas + openpyxl
    # ===========================================================================

    @staticmethod
    def generate_excel_rentabilidad(fecha_inicio, fecha_fin):
        """
        Genera un archivo Excel con el reporte de rentabilidad.

        Convierte los datos de rentabilidad (procesados con margen_porcentaje)
        a un DataFrame de pandas y lo escribe en un buffer BytesIO en formato .xlsx.

        Args:
            fecha_inicio (str|None): Fecha inicio del rango.
            fecha_fin    (str|None): Fecha fin del rango.

        Returns:
            BytesIO: Buffer con el archivo Excel listo para enviar con `send_file()`.
        """
        datos = ReporteService.get_datos_rentabilidad(fecha_inicio, fecha_fin)
        import pandas as pd
        df = pd.DataFrame(datos)
        output = BytesIO()
        # `ExcelWriter` con `openpyxl` es el motor recomendado para archivos .xlsx modernos
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Rentabilidad")
        output.seek(0)  # Regresar al inicio del buffer para que send_file pueda leerlo
        return output

    @staticmethod
    def generate_excel_pedidos(fecha_inicio, fecha_fin):
        """
        Genera un archivo Excel con el reporte de pedidos.

        Obtiene los datos directamente del repositorio como DataFrame
        (usando pd.read_sql) para mayor eficiencia.

        Args:
            fecha_inicio (str|None): Fecha inicio del rango.
            fecha_fin    (str|None): Fecha fin del rango.

        Returns:
            BytesIO: Buffer con el archivo Excel listo para enviar.
        """
        df = PedidoRepository.get_pedidos_report_excel(fecha_inicio, fecha_fin)
        import pandas as pd
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Pedidos")
        output.seek(0)
        return output

    @staticmethod
    def generate_excel_produccion(fecha_inicio, fecha_fin):
        """
        Genera un archivo Excel con el reporte de producción/materiales usados.

        Args:
            fecha_inicio (str|None): Fecha inicio del rango.
            fecha_fin    (str|None): Fecha fin del rango.

        Returns:
            BytesIO: Buffer con el archivo Excel.
        """
        df = ProduccionRepository.get_produccion_report_excel(fecha_inicio, fecha_fin)
        import pandas as pd
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Produccion")
        output.seek(0)
        return output

    @staticmethod
    def generate_excel_inventario():
        """
        Genera un archivo Excel con el estado actual del inventario.

        No requiere filtros de fecha (es una foto del estado actual).

        Returns:
            BytesIO: Buffer con el archivo Excel.
        """
        df = MaterialRepository.get_inventory_report()
        import pandas as pd
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventario")
        output.seek(0)
        return output

    # ===========================================================================
    # EXPORTACIONES A PDF usando reportlab
    # ===========================================================================

    @staticmethod
    def generate_pdf_pedidos(fecha_inicio, fecha_fin):
        """
        Genera un PDF con la tabla de pedidos en el rango de fechas.

        Estructura del PDF:
        1. Encabezado (_add_pdf_header): Logo + título + fecha de generación.
        2. Tabla de datos (_build_pdf_table): Filas de pedidos estilizadas.

        Las celdas de texto largo se truncan para que quepan en la hoja.

        Args:
            fecha_inicio (str|None): Fecha inicio del rango.
            fecha_fin    (str|None): Fecha fin del rango.

        Returns:
            BytesIO: Buffer con el archivo PDF.
        """
        pedidos = PedidoRepository.get_pedidos_report_pdf(fecha_inicio, fecha_fin)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = ReporteService._add_pdf_header([], "Reporte de Pedidos")

        # Cabecera de la tabla
        data = [["ID", "Cliente", "Estado", "Fecha", "Valor ($)"]]
        for p in pedidos:
            data.append([
                p.get("id", ""),
                str(p.get("cliente", ""))[:20],          # Truncar a 20 chars
                p.get("estado", "").upper(),
                str(p.get("fecha_creacion", ""))[:10],   # Solo la fecha, sin hora
                f"${p.get('valor_total', 0):,.2f}"
            ])

        elements.append(ReporteService._build_pdf_table(data))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_pdf_produccion(fecha_inicio, fecha_fin):
        """
        Genera un PDF con el detalle de materiales usados en producción.

        Args:
            fecha_inicio (str|None): Fecha inicio del rango.
            fecha_fin    (str|None): Fecha fin del rango.

        Returns:
            BytesIO: Buffer con el archivo PDF.
        """
        registros = ProduccionRepository.get_produccion_report_pdf(fecha_inicio, fecha_fin)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = ReporteService._add_pdf_header([], "Reporte de Producción (Materiales Usados)")

        data = [["Pedido", "Fecha", "Material", "Cantidad", "Costo Total ($)"]]
        for r in registros:
            data.append([
                f"#{r.get('pedido_id', '')}",
                str(r.get("fecha_creacion", ""))[:10],
                str(r.get("material", ""))[:25],
                str(r.get("cantidad_usada", "")),
                f"${r.get('costo_total', 0):,.2f}"
            ])

        elements.append(ReporteService._build_pdf_table(data))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_pdf_inventario():
        """
        Genera un PDF con el estado actual del inventario, indicando si
        cada material está en stock normal u OK vs. BAJO STOCK.

        El estado se calcula aquí en Python: si stock_actual > stock_minimo
        es "OK", de lo contrario es "BAJO STOCK".

        Returns:
            BytesIO: Buffer con el archivo PDF.
        """
        materiales = MaterialRepository.get_inventory_list_for_pdf()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = ReporteService._add_pdf_header([], "Estado Actual de Inventario")

        data = [["Material", "Stock Actual", "Stock Mínimo", "Precio Compra ($)", "Estado"]]
        for m in materiales:
            # Calcular el estado de stock en Python para mostrar en la tabla PDF
            estado = "OK" if m.get("stock_actual", 0) > m.get("stock_minimo", 0) else "BAJO STOCK"
            data.append([
                str(m.get("nombre", ""))[:30],
                str(m.get("stock_actual", "")),
                str(m.get("stock_minimo", "")),
                f"${m.get('precio_compra', 0):,.2f}",
                estado
            ])

        elements.append(ReporteService._build_pdf_table(data))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ===========================================================================
    # MÉTODOS PRIVADOS AUXILIARES PARA GENERACIÓN DE PDF
    # ===========================================================================

    @staticmethod
    def _add_pdf_header(elements, title_text):
        """
        Construye y agrega los elementos del encabezado estándar a un PDF.

        El encabezado incluye (en orden):
        1. Logo de CAMBRIX (si existe el archivo `app/static/img/logo.png`).
           Si no existe, se omite silenciosamente sin romper el PDF.
        2. Título del reporte (en negrita, estilo "Title" de reportlab).
        3. Fecha y hora de generación del reporte.
        4. Espacio vertical separador.

        Args:
            elements  (list):  Lista de elementos reportlab a la que se agregan los del header.
            title_text(str):   Texto del título del reporte (ej. "Reporte de Pedidos").

        Returns:
            list: La misma lista `elements` con los elementos del encabezado agregados.
        """
        styles = getSampleStyleSheet()
        # Intentar incluir el logo de la empresa
        logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=120, height=60)
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 10))
            except Exception:
                # Si el logo no puede cargarse (ej. formato incorrecto),
                # continuar sin él en lugar de romper la generación del PDF
                pass

        # Título del reporte en HTML-style bold dentro de Paragraph
        titulo = Paragraph(f"<b>CAMBRIX</b> - {title_text}", styles["Title"])
        # Fecha y hora exacta de generación del documento
        fecha = Paragraph(
            f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"]
        )
        elements.append(titulo)
        elements.append(fecha)
        elements.append(Spacer(1, 20))
        return elements

    @staticmethod
    def _build_pdf_table(data, col_widths=None):
        """
        Crea y estiliza una tabla de reportlab con el diseño corporativo de CAMBRIX.

        Estilo aplicado:
        - Encabezado (fila 0): Fondo azul corporativo (#029EF2), texto blanco, negrita.
        - Filas de datos: Fondo blanco con filas alternas en gris muy claro (#f4f7fe).
        - Alineación: Centrado en todas las celdas.
        - Bordes: Grid completo con líneas en gris claro.

        Args:
            data      (list[list]): Datos de la tabla. La primera fila es el encabezado.
            col_widths(list|None):  Anchos de columna. Si None, reportlab los calcula automáticamente.

        Returns:
            reportlab.platypus.Table: Objeto tabla listo para agregar al documento PDF.
        """
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Fila de encabezado: fondo azul corporativo, texto blanco
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#029EF2")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            # Alineación centrada para todas las celdas
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            # Encabezado en negrita
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Filas de datos: fondo blanco
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            # Bordes grises para toda la tabla
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            # Filas alternas con fondo gris muy claro para mejorar legibilidad
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fe")]),
        ]))
        return table
