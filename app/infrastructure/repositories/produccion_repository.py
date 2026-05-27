from app.infrastructure.database import get_connection
import pandas as pd

class ProduccionRepository:
    @staticmethod
    def get_costo_total_by_pedido(pedido_id):
        """Retorna la suma de costo_total de todos los materiales ya asignados al pedido."""
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT COALESCE(SUM(costo_total), 0) AS total
            FROM produccion_materiales
            WHERE pedido_id = %s
        """, (pedido_id,))
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return float(res["total"]) if res else 0.0

    @staticmethod
    def get_by_pedido(pedido_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT pm.*, m.nombre
            FROM produccion_materiales pm
            JOIN materiales m ON pm.material_id = m.id
            WHERE pm.pedido_id=%s
        """, (pedido_id,))
        usados = cursor.fetchall()
        cursor.close()
        connection.close()
        return usados

    @staticmethod
    def create(pedido_id, material_id, cantidad_usada, costo_unitario, costo_total):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO produccion_materiales
            (pedido_id, material_id, cantidad_usada, costo_unitario, costo_total)
            VALUES (%s, %s, %s, %s, %s)
        """, (pedido_id, material_id, cantidad_usada, costo_unitario, costo_total))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def get_top_materiales():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.nombre, SUM(pm.cantidad_usada) as total_usado
            FROM produccion_materiales pm
            JOIN materiales m ON pm.material_id = m.id
            GROUP BY pm.material_id
            ORDER BY total_usado DESC
            LIMIT 5
        """)
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_report_query(base_query, date_col, fecha_inicio, fecha_fin):
        params = []
        where_started = "WHERE" in base_query.upper()
        
        if fecha_inicio:
            connector = "AND" if where_started else "WHERE"
            base_query += f" {connector} {date_col} >= %s "
            params.append(fecha_inicio + " 00:00:00")
            where_started = True
            
        if fecha_fin:
            connector = "AND" if where_started else "WHERE"
            base_query += f" {connector} {date_col} <= %s "
            params.append(fecha_fin + " 23:59:59")
            
        return base_query, tuple(params)

    @staticmethod
    def get_produccion_report_excel(fecha_inicio, fecha_fin):
        connection = get_connection()
        base_query = """
        SELECT pm.id, pm.pedido_id, m.nombre AS material, pm.cantidad_usada, pm.costo_unitario, pm.costo_total, p.fecha_creacion
        FROM produccion_materiales pm
        JOIN materiales m ON pm.material_id = m.id
        JOIN pedidos p ON pm.pedido_id = p.id
        """
        query, params = ProduccionRepository.get_report_query(base_query, "p.fecha_creacion", fecha_inicio, fecha_fin)
        df = pd.read_sql(query, connection, params=params)
        connection.close()
        return df

    @staticmethod
    def get_produccion_report_pdf(fecha_inicio, fecha_fin):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        base_query = """
        SELECT pm.pedido_id, m.nombre AS material, pm.cantidad_usada, pm.costo_total, p.fecha_creacion
        FROM produccion_materiales pm
        JOIN materiales m ON pm.material_id = m.id
        JOIN pedidos p ON pm.pedido_id = p.id
        """
        query, params = ProduccionRepository.get_report_query(base_query, "p.fecha_creacion", fecha_inicio, fecha_fin)
        cursor.execute(query, params)
        registros = cursor.fetchall()
        cursor.close()
        connection.close()
        return registros
