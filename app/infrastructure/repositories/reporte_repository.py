"""
app/infrastructure/repositories/reporte_repository.py - Repositorio de Reportes
=================================================================================
Responsabilidad: Contiene las consultas SQL especializadas para la generación
de datos en los módulos de reportes. A diferencia de los otros repositorios
(que soportan operaciones CRUD), este repositorio es de SOLO LECTURA y sus
consultas están diseñadas para ser consumidas por tablas de datos interactivas
(DataTables) en el frontend vía API JSON.

Reportes disponibles:
    1. Pedidos:       Lista de pedidos con filtros de fecha y estado.
    2. Producción:    Detalle de materiales usados por pedido.
    3. Inventario:    Valuación del inventario actual (precio * stock).
    4. Rentabilidad:  Análisis financiero por pedido (margen bruto estimado).
    5. Trazabilidad:  Historial de movimientos de inventario para auditoría.

Lógica de Rentabilidad (Reporte #4):
    El margen bruto se calcula con una fórmula estimada:
    margen_bruto = valor_total - costo_materia_prima - costo_operativo_estimado
    Donde:
        - costo_materia_prima     = SUM(produccion_materiales.costo_total)
        - costo_operativo_estimado = valor_total * 0.15 (15% estimado de gastos fijos)
    Este porcentaje (15%) es una estimación simplificada. Para mayor precisión,
    debería configurarse en la base de datos o como variable de entorno.
"""
from app.infrastructure.database import get_connection


class ReporteRepository:
    """
    Clase de repositorio estático para las consultas de reportes (solo lectura).
    """

    @staticmethod
    def get_datos_pedidos(fecha_inicio, fecha_fin, estado):
        """
        Obtiene los datos de pedidos para el reporte de ventas/pedidos.

        Construye una consulta dinámica combinando datos de `pedidos`, `clientes`
        y `usuarios` (el vendedor/responsable). Soporta filtros opcionales de
        fecha de creación y estado del pedido.

        Args:
            fecha_inicio (str | None): Fecha inicio en formato 'YYYY-MM-DD'.
            fecha_fin    (str | None): Fecha fin en formato 'YYYY-MM-DD'.
            estado       (str | None): Estado del pedido a filtrar. None = todos.

        Returns:
            list[dict]: Lista de pedidos con campos: id, fecha_creacion, fecha_entrega,
                        cliente, vendedor, valor_total, estado. Ordenados por fecha DESC.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        # Consulta base con JOINs para obtener nombres legibles en lugar de IDs
        query = """
            SELECT p.id, p.fecha_creacion, p.fecha_entrega, c.nombre as cliente,
                   u.nombre as vendedor, p.valor_total, p.estado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN usuarios u ON p.responsable_id = u.id
            WHERE 1=1
        """
        params = []
        # Filtros dinámicos: solo se agregan si el parámetro tiene valor
        if fecha_inicio:
            query += " AND p.fecha_creacion >= %s"
            params.append(f"{fecha_inicio} 00:00:00")
        if fecha_fin:
            query += " AND p.fecha_creacion <= %s"
            params.append(f"{fecha_fin} 23:59:59")
        if estado:
            query += " AND p.estado = %s"
            params.append(estado)

        query += " ORDER BY p.fecha_creacion DESC"
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()
        return datos

    @staticmethod
    def get_datos_produccion(fecha_inicio, fecha_fin):
        """
        Obtiene el detalle de producción (materiales usados por pedido) para el reporte.

        Combina `produccion_materiales`, `pedidos`, `materiales` y `usuarios`
        para presentar una vista completa de cada registro de producción,
        incluyendo el operario asignado.

        Args:
            fecha_inicio (str | None): Fecha inicio basada en la fecha de creación del pedido.
            fecha_fin    (str | None): Fecha fin.

        Returns:
            list[dict]: Lista con campos: id (pedido), fecha_inicio (creación del pedido),
                        fecha_fin_real (entrega), producto (material), operario_asignado,
                        cantidad_usada, costo_total, estado.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT pm.pedido_id as id, p.fecha_creacion as fecha_inicio,
                   p.fecha_entrega as fecha_fin_real, m.nombre as producto,
                   u.nombre as operario_asignado, pm.cantidad_usada, pm.costo_total, p.estado
            FROM produccion_materiales pm
            JOIN pedidos p ON pm.pedido_id = p.id
            JOIN materiales m ON pm.material_id = m.id
            LEFT JOIN usuarios u ON p.responsable_id = u.id
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            query += " AND p.fecha_creacion >= %s"
            params.append(f"{fecha_inicio} 00:00:00")
        if fecha_fin:
            query += " AND p.fecha_creacion <= %s"
            params.append(f"{fecha_fin} 23:59:59")

        query += " ORDER BY p.fecha_creacion DESC"
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()
        return datos

    @staticmethod
    def get_datos_inventario():
        """
        Obtiene la valuación completa del inventario actual.

        Calcula el `valor_total` de cada material como:
        stock_actual * costo_unitario

        No tiene filtros de fecha porque representa el estado ACTUAL del
        inventario, no un histórico.

        Returns:
            list[dict]: Lista de materiales con campos: codigo (id), nombre,
                        saldo_final (stock_actual), stock_minimo,
                        valor_unitario (costo_unitario), valor_total (calculado).
                        Ordenados alfabéticamente.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT m.id as codigo, m.nombre, m.stock_actual as saldo_final,
                   m.stock_minimo, m.costo_unitario as valor_unitario,
                   (m.stock_actual * m.costo_unitario) as valor_total
            FROM materiales m
            ORDER BY m.nombre ASC
        """
        cursor.execute(query)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()
        return datos

    @staticmethod
    def get_datos_rentabilidad(fecha_inicio, fecha_fin):
        """
        Obtiene el análisis de rentabilidad estimada por pedido.

        Lógica de cálculo (aplicada en SQL):
            - ingreso_neto:           valor_total del pedido.
            - costo_materia_prima:    SUM de costo_total en produccion_materiales
                                      (LEFT JOIN, puede ser 0 si no hay producción).
            - costo_operativo_estimado: valor_total * 0.15 (gastos fijos estimados al 15%).
            - margen_bruto:           ingreso_neto - costo_materia_prima - costo_operativo.

        Solo incluye pedidos con estados productivos:
        'entregado', 'terminado', 'aprobado', 'en_produccion'.

        El porcentaje de margen (`margen_porcentaje`) se calcula en
        `ReporteService` después de recibir estos datos.

        Args:
            fecha_inicio (str | None): Fecha inicio de creación del pedido.
            fecha_fin    (str | None): Fecha fin.

        Returns:
            list[dict]: Lista de pedidos con análisis financiero, agrupados por
                        pedido (GROUP BY p.id). Campos: pedido_id, cliente,
                        ingreso_neto, costo_materia_prima, costo_operativo_estimado,
                        margen_bruto, fecha_creacion.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT p.id as pedido_id, c.nombre as cliente, p.valor_total as ingreso_neto,
                   IFNULL(SUM(pm.costo_total), 0) as costo_materia_prima,
                   (p.valor_total * 0.15) as costo_operativo_estimado,
                   p.valor_total - IFNULL(SUM(pm.costo_total), 0) - (p.valor_total * 0.15) as margen_bruto,
                   p.fecha_creacion
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN produccion_materiales pm ON p.id = pm.pedido_id
            WHERE p.estado IN ('entregado', 'terminado', 'aprobado', 'en_produccion')
        """
        params = []
        if fecha_inicio:
            query += " AND p.fecha_creacion >= %s"
            params.append(f"{fecha_inicio} 00:00:00")
        if fecha_fin:
            query += " AND p.fecha_creacion <= %s"
            params.append(f"{fecha_fin} 23:59:59")

        # GROUP BY necesario porque usamos SUM() y tenemos LEFT JOIN con produccion_materiales
        query += " GROUP BY p.id ORDER BY p.fecha_creacion DESC"
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()
        return datos

    @staticmethod
    def get_datos_trazabilidad(fecha_inicio, fecha_fin):
        """
        Obtiene el historial de movimientos de inventario para el reporte de auditoría.

        Este reporte permite rastrear cada cambio en el inventario (quién hizo qué
        y cuándo), respondiendo preguntas de auditoría como:
        "¿Qué pasó con el stock del material X entre las fechas Y y Z?"

        Limitado a los últimos 100 registros por razones de rendimiento.
        Para un sistema de auditoría completo, se recomendaría paginación.

        Args:
            fecha_inicio (str | None): Fecha inicio del rango de auditoría.
            fecha_fin    (str | None): Fecha fin del rango de auditoría.

        Returns:
            list[dict]: Lista de hasta 100 movimientos recientes con campos:
                        fecha_hora, usuario (siempre "Sistema"), accion (tipo),
                        modulo (siempre "Inventario"), detalle (descripción concatenada).
                        Ordenados del más reciente al más antiguo.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT mi.fecha as fecha_hora, 'Sistema' as usuario, mi.tipo as accion,
                   'Inventario' as modulo,
                   CONCAT('Movimiento de ', m.nombre, ': ', mi.motivo, ' (', mi.cantidad, ')') as detalle
            FROM movimientos_inventario mi
            JOIN materiales m ON mi.material_id = m.id
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            query += " AND mi.fecha >= %s"
            params.append(f"{fecha_inicio} 00:00:00")
        if fecha_fin:
            query += " AND mi.fecha <= %s"
            params.append(f"{fecha_fin} 23:59:59")

        # LIMIT 100 para no sobrecargar la respuesta; considerar paginación en futuras versiones
        query += " ORDER BY mi.fecha DESC LIMIT 100"
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()
        return datos
