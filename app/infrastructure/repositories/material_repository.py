from app.infrastructure.database import get_connection

class MaterialRepository:
    @staticmethod
    def get_all(stock_status=None, categoria=None):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM materiales WHERE 1=1"
        params = []
        
        if stock_status == 'critico':
            query += " AND stock_actual <= stock_minimo"
        elif stock_status == 'normal':
            query += " AND stock_actual > stock_minimo"
            
        if categoria:
            query += " AND categoria = %s"
            params.append(categoria)
            
        query += " ORDER BY nombre"
        
        cursor.execute(query, tuple(params))
        materiales = cursor.fetchall()
        cursor.close()
        connection.close()
        return materiales

    @staticmethod
    def get_categorias():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT categoria FROM materiales ORDER BY categoria")
        categorias = cursor.fetchall()
        cursor.close()
        connection.close()
        return [c["categoria"] for c in categorias if c["categoria"]]

    @staticmethod
    def get_by_id(id):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM materiales WHERE id=%s", (id,))
        material = cursor.fetchone()
        cursor.close()
        connection.close()
        return material

    @staticmethod
    def get_low_stock():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT nombre, stock_actual, stock_minimo
            FROM materiales
            WHERE stock_actual <= stock_minimo
            ORDER BY stock_actual ASC
        """)
        materiales = cursor.fetchall()
        cursor.close()
        connection.close()
        return materiales

    @staticmethod
    def count_low_stock():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS bajos FROM materiales WHERE stock_actual <= stock_minimo")
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()
        return resultado

    @staticmethod
    def get_total_count():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM materiales")
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()
        return resultado["total"]

    @staticmethod
    def create(nombre, categoria, unidad_medida, stock_actual, stock_minimo, costo_unitario):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO materiales
            (nombre, categoria, unidad_medida, stock_actual, stock_minimo, costo_unitario)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, categoria, unidad_medida, stock_actual, stock_minimo, costo_unitario))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def update(id, nombre, categoria, unidad_medida, stock_minimo, costo_unitario):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE materiales
            SET nombre=%s, categoria=%s, unidad_medida=%s, stock_minimo=%s, costo_unitario=%s
            WHERE id=%s
        """, (nombre, categoria, unidad_medida, stock_minimo, costo_unitario, id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def update_stock(id, nuevo_stock):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE materiales SET stock_actual=%s WHERE id=%s", (nuevo_stock, id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def delete(id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM produccion_materiales WHERE material_id=%s", (id,))
            cursor.execute("DELETE FROM movimientos_inventario WHERE material_id=%s", (id,))
            cursor.execute("DELETE FROM materiales WHERE id=%s", (id,))
            connection.commit()
            success = True
            error_msg = None
        except Exception as e:
            connection.rollback()
            success = False
            error_msg = str(e)
        finally:
            cursor.close()
            connection.close()
        return success, error_msg

    @staticmethod
    def get_inventory_report():
        import pandas as pd
        connection = get_connection()
        df = pd.read_sql("SELECT id, nombre, stock_actual, stock_minimo, precio_compra FROM materiales", connection)
        connection.close()
        return df

    @staticmethod
    def get_inventory_list_for_pdf():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT nombre, stock_actual, stock_minimo, precio_compra FROM materiales ORDER BY nombre")
        materiales = cursor.fetchall()
        cursor.close()
        connection.close()
        return materiales
