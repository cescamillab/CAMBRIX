from app.db import get_connection
import pandas as pd

class PedidoModel:
    @staticmethod
    def count_total():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM pedidos")
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] if res else 0

    @staticmethod
    def count_by_status(status):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS count FROM pedidos WHERE estado = %s", (status,))
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["count"] if res else 0

    @staticmethod
    def sum_total_invoiced():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT SUM(valor_total) AS total FROM pedidos")
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def sum_total_pending_balance():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT SUM(valor_total - anticipo) AS total FROM pedidos")
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def group_by_status():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT estado, COUNT(*) as total FROM pedidos GROUP BY estado")
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_monthly_income():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT DATE_FORMAT(fecha_creacion, '%Y-%m') as mes, SUM(valor_total) as total_mes
            FROM pedidos GROUP BY mes ORDER BY mes
        """)
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    # === FOR EMPLOYEES ===
    @staticmethod
    def count_total_for_user(user_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM pedidos WHERE responsable_id = %s", (user_id,))
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] if res else 0

    @staticmethod
    def count_by_status_for_user(user_id, status):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS count FROM pedidos WHERE responsable_id = %s AND estado = %s", (user_id, status))
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["count"] if res else 0

    @staticmethod
    def sum_total_invoiced_for_user(user_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT SUM(valor_total) AS total FROM pedidos WHERE responsable_id = %s", (user_id,))
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def sum_total_pending_balance_for_user(user_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT SUM(valor_total - anticipo) AS total FROM pedidos WHERE responsable_id = %s", (user_id,))
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def group_by_status_for_user(user_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT estado, COUNT(*) as total FROM pedidos WHERE responsable_id = %s GROUP BY estado", (user_id,))
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_monthly_income_for_user(user_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT DATE_FORMAT(fecha_creacion, '%Y-%m') as mes, SUM(valor_total) as total_mes
            FROM pedidos WHERE responsable_id = %s GROUP BY mes ORDER BY mes
        """, (user_id,))
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_top_clientes():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.nombre, SUM(p.valor_total) as total_facturado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            GROUP BY p.cliente_id
            ORDER BY total_facturado DESC
            LIMIT 5
        """)
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_latest():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, c.nombre as cliente, p.valor_total, p.estado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.fecha_creacion DESC
            LIMIT 5
        """)
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_latest_for_user(user_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, c.nombre as cliente, p.valor_total, p.estado
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.responsable_id = %s
            ORDER BY p.fecha_creacion DESC
            LIMIT 5
        """, (user_id,))
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    # === CRUD ===
    @staticmethod
    def filter_pedidos(role, user_id, busqueda, estado, responsable, fecha_inicio=None, fecha_fin=None, orden_id=None, orden_fecha=None):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT pedidos.*, clientes.nombre AS cliente_nombre,
            usuarios.nombre AS responsable_nombre,
            (pedidos.valor_total - pedidos.anticipo) AS saldo
            FROM pedidos
            JOIN clientes ON pedidos.cliente_id = clientes.id
            LEFT JOIN usuarios ON pedidos.responsable_id = usuarios.id
            WHERE 1=1
        """
        params = []
        if role != "jefe":
            query += " AND pedidos.responsable_id = %s"
            params.append(user_id)
        if busqueda:
            query += " AND clientes.nombre LIKE %s"
            params.append(f"%{busqueda}%")
        if estado:
            query += " AND pedidos.estado = %s"
            params.append(estado)
        if responsable and role == "jefe":
            query += " AND pedidos.responsable_id = %s"
            params.append(responsable)
        
        # Filtro de Fechas
        if fecha_inicio:
            query += " AND pedidos.fecha_entrega >= %s"
            params.append(f"{fecha_inicio} 00:00:00")
        if fecha_fin:
            query += " AND pedidos.fecha_entrega <= %s"
            params.append(f"{fecha_fin} 23:59:59")
            
        # Ordenamiento
        # order clauses list
        order_clauses = []
        
        if orden_id in ['asc', 'desc']:
            order_clauses.append(f"pedidos.id {orden_id.upper()}")
            
        if orden_fecha in ['asc', 'desc']:
            order_clauses.append(f"pedidos.fecha_entrega {orden_fecha.upper()}")
            
        if order_clauses:
            query += " ORDER BY " + ", ".join(order_clauses)
        else:
            query += " ORDER BY pedidos.fecha_creacion DESC"

        cursor.execute(query, params)
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def create(cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO pedidos 
            (cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id))
        connection.commit()
        pedido_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return pedido_id

    @staticmethod
    def get_by_id(pedido_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
        pedido = cursor.fetchone()
        cursor.close()
        connection.close()
        return pedido

    @staticmethod
    def get_detail_by_id(pedido_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                pedidos.*, 
                clientes.nombre AS cliente_nombre,
                clientes.telefono,
                clientes.correo,
                usuarios.username AS responsable_nombre,
                (pedidos.valor_total - pedidos.anticipo) AS saldo
            FROM pedidos
            JOIN clientes ON pedidos.cliente_id = clientes.id
            LEFT JOIN usuarios ON pedidos.responsable_id = usuarios.id
            WHERE pedidos.id = %s
        """, (pedido_id,))
        pedido = cursor.fetchone()
        cursor.close()
        connection.close()
        return pedido

    @staticmethod
    def update_estado(pedido_id, nuevo_estado):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, pedido_id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def update(pedido_id, cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE pedidos
            SET cliente_id=%s, descripcion=%s, fecha_entrega=%s,
                valor_total=%s, anticipo=%s, responsable_id=%s
            WHERE id=%s
        """, (cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id, pedido_id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def delete(pedido_id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
        connection.commit()
        cursor.close()
        connection.close()

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
    def get_pedidos_report_excel(fecha_inicio, fecha_fin):
        connection = get_connection()
        query, params = PedidoModel.get_report_query("SELECT * FROM pedidos", "fecha_creacion", fecha_inicio, fecha_fin)
        df = pd.read_sql(query, connection, params=params)
        connection.close()
        return df

    @staticmethod
    def get_pedidos_report_pdf(fecha_inicio, fecha_fin):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        base_query = """
            SELECT pedidos.id, clientes.nombre AS cliente, pedidos.estado, pedidos.fecha_creacion, pedidos.valor_total
            FROM pedidos
            JOIN clientes ON pedidos.cliente_id = clientes.id
        """
        query, params = PedidoModel.get_report_query(base_query, "pedidos.fecha_creacion", fecha_inicio, fecha_fin)
        cursor.execute(query, params)
        pedidos = cursor.fetchall()
        cursor.close()
        connection.close()
        return pedidos
