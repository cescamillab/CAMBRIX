from app.db import get_connection

class MovimientoModel:
    @staticmethod
    def create(material_id, tipo, cantidad, motivo, pedido_id=None):
        connection = get_connection()
        cursor = connection.cursor()
        if pedido_id:
            cursor.execute("""
                INSERT INTO movimientos_inventario
                (material_id, tipo, cantidad, motivo, pedido_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (material_id, tipo, cantidad, motivo, pedido_id))
        else:
            cursor.execute("""
                INSERT INTO movimientos_inventario
                (material_id, tipo, cantidad, motivo)
                VALUES (%s, %s, %s, %s)
            """, (material_id, tipo, cantidad, motivo))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def get_by_material(material_id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*, p.id AS pedido_relacionado
            FROM movimientos_inventario m
            LEFT JOIN pedidos p ON m.pedido_id = p.id
            WHERE m.material_id=%s
            ORDER BY m.fecha DESC
        """, (material_id,))
        movimientos = cursor.fetchall()
        cursor.close()
        connection.close()
        return movimientos
