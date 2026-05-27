from app.infrastructure.database import get_connection

class ReporteRepository:
    @staticmethod
    def get_datos_pedidos(fecha_inicio, fecha_fin, estado):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT p.id, p.fecha_creacion, p.fecha_entrega, c.nombre as cliente,
                   u.nombre as vendedor, p.valor_total, p.estado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
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
            
        query += " GROUP BY p.id ORDER BY p.fecha_creacion DESC"
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()
        return datos

    @staticmethod
    def get_datos_trazabilidad(fecha_inicio, fecha_fin):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT mi.fecha as fecha_hora, 'Sistema' as usuario, mi.tipo as accion,
                   'Inventario' as modulo, CONCAT('Movimiento de ', m.nombre, ': ', mi.motivo, ' (', mi.cantidad, ')') as detalle
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
            
        query += " ORDER BY mi.fecha DESC LIMIT 100"
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()
        return datos
