"""
app/infrastructure/repositories/material_repository.py - Repositorio de Materiales
=====================================================================================
Responsabilidad: Encapsula TODAS las operaciones de base de datos sobre la
tabla `materiales`. Es el repositorio más completo del sistema, con funciones
de lectura, escritura, filtrado y generación de reportes.

Tabla gestionada: `materiales`
    Columnas principales:
        - id:             Identificador único auto-incrementado.
        - nombre:         Nombre descriptivo del material (ej. "Madera Pino 1x4").
        - categoria:      Agrupación del material (ej. "Madera", "Herraje").
        - unidad_medida:  Unidad en que se mide (ej. "ml", "unidad", "kg").
        - stock_actual:   Cantidad disponible actualmente en bodega.
        - stock_minimo:   Umbral de alerta. Cuando stock_actual <= stock_minimo,
                          el sistema muestra una alerta de reabastecimiento.
        - costo_unitario: Costo de compra por unidad del material.

Lógica de "stock bajo":
    Un material se considera en STOCK CRÍTICO cuando:
    `stock_actual <= stock_minimo`
    Esta condición es verificada en múltiples consultas (get_low_stock,
    count_low_stock) y mostrada en el Dashboard y en la lista de materiales.
"""
from app.infrastructure.database import get_connection


class MaterialRepository:
    """
    Clase de repositorio estático para la tabla `materiales`.
    """

    @staticmethod
    def get_all(stock_status=None, categoria=None):
        """
        Obtiene la lista de materiales, con filtros opcionales de stock y categoría.

        Construye la consulta SQL dinámicamente según los filtros recibidos.
        Parte de una base `WHERE 1=1` (siempre verdadero) para poder agregar
        condiciones AND de forma segura sin preocuparse por la primera condición.

        Args:
            stock_status (str | None): Filtro de stock.
                - "critico": Solo materiales con stock_actual <= stock_minimo.
                - "normal":  Solo materiales con stock_actual > stock_minimo.
                - None:      Sin filtro de stock (muestra todos).
            categoria (str | None): Si se provee, filtra por la categoría exacta.
                                    Si es None o vacío, no filtra por categoría.

        Returns:
            list[dict]: Lista de todos los materiales que cumplen los filtros,
                        ordenados alfabéticamente por nombre.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        # Base de la consulta. "WHERE 1=1" es un truco para simplificar
        # la concatenación de condiciones AND dinámicas.
        query = "SELECT * FROM materiales WHERE 1=1"
        params = []

        # Filtro de estado de stock
        if stock_status == 'critico':
            query += " AND stock_actual <= stock_minimo"
        elif stock_status == 'normal':
            query += " AND stock_actual > stock_minimo"

        # Filtro de categoría (solo si se proporcionó un valor)
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
        """
        Obtiene la lista de categorías únicas existentes en el inventario.

        Usado para poblar el filtro de "Categoría" en la vista de lista de
        materiales, mostrando solo las categorías que existen actualmente.

        Returns:
            list[str]: Lista de strings con los nombres de categorías únicas,
                       ordenadas alfabéticamente. Los valores NULL se excluyen.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT categoria FROM materiales ORDER BY categoria")
        categorias = cursor.fetchall()
        cursor.close()
        connection.close()
        # Extraer solo el string del nombre de cada fila y filtrar valores None
        return [c["categoria"] for c in categorias if c["categoria"]]

    @staticmethod
    def get_by_id(id):
        """
        Busca y retorna un material específico por su ID.

        Args:
            id (int): ID del material a buscar.

        Returns:
            dict | None: Diccionario con todos los campos del material si existe,
                         o None si no se encontró ningún material con ese ID.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM materiales WHERE id=%s", (id,))
        material = cursor.fetchone()
        cursor.close()
        connection.close()
        return material

    @staticmethod
    def get_low_stock():
        """
        Obtiene los materiales que están en stock crítico (stock_actual <= stock_minimo).

        Usado en el Dashboard para mostrar la alerta de materiales que necesitan
        reabastecimiento urgente.

        Returns:
            list[dict]: Lista de materiales en stock crítico, con los campos
                        nombre, stock_actual y stock_minimo, ordenados por
                        stock_actual ascendente (el más crítico primero).
        """
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
        """
        Cuenta cuántos materiales tienen stock crítico.

        Usado en la vista de inventario para mostrar la insignia (badge) de
        alerta en el encabezado de la tabla.

        Returns:
            dict: Diccionario con la clave "bajos" y el conteo como valor.
                  Ej: {"bajos": 3}
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) AS bajos FROM materiales WHERE stock_actual <= stock_minimo"
        )
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()
        return resultado

    @staticmethod
    def get_total_count():
        """
        Cuenta el total de materiales registrados en el inventario.

        Usado en la página de reportes para mostrar el KPI de materiales totales.

        Returns:
            int: Número total de materiales en la tabla.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM materiales")
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()
        return resultado["total"]

    @staticmethod
    def create(nombre, categoria, unidad_medida, stock_actual, stock_minimo, costo_unitario):
        """
        Inserta un nuevo material en el catálogo de inventario.

        Args:
            nombre        (str):   Nombre descriptivo del material.
            categoria     (str):   Categoría de agrupación (ej. "Madera").
            unidad_medida (str):   Unidad de medida (ej. "ml", "kg", "unidad").
            stock_actual  (float): Cantidad inicial disponible en bodega.
            stock_minimo  (float): Nivel mínimo antes de disparar la alerta.
            costo_unitario(float): Precio de costo por unidad del material.

        Returns:
            None.
        """
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
        """
        Actualiza los datos de un material existente.

        IMPORTANTE: Este método NO actualiza el `stock_actual`. La cantidad
        de stock solo se modifica a través de `update_stock()`, que es llamado
        después de registrar un movimiento de inventario. Esto garantiza que
        cada cambio de stock quede auditado en `movimientos_inventario`.

        Args:
            id            (int):   ID del material a actualizar.
            nombre        (str):   Nuevo nombre.
            categoria     (str):   Nueva categoría.
            unidad_medida (str):   Nueva unidad de medida.
            stock_minimo  (float): Nuevo nivel mínimo de alerta.
            costo_unitario(float): Nuevo costo unitario.

        Returns:
            None.
        """
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
        """
        Actualiza ÚNICAMENTE el `stock_actual` de un material.

        Es un método de propósito único (Single Responsibility). Solo debe
        llamarse DESPUÉS de que el movimiento correspondiente ya fue registrado
        en `movimientos_inventario` por `MovimientoRepository.create()`.

        Args:
            id          (int):   ID del material cuyo stock se va a actualizar.
            nuevo_stock (float): El nuevo valor calculado de stock.
                                 Ej: stock_anterior + cantidad_entrada
                                 Ej: stock_anterior - cantidad_salida

        Returns:
            None.
        """
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE materiales SET stock_actual=%s WHERE id=%s", (nuevo_stock, id)
        )
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def delete(id):
        """
        Elimina un material y todos sus registros dependientes de la base de datos.

        Para mantener la integridad referencial (y evitar errores de clave foránea),
        el borrado se realiza en cascada manual:
        1. Primero elimina los registros de producción que referencian al material.
        2. Luego elimina los movimientos de inventario del material.
        3. Finalmente elimina el material en sí.

        Si ocurre cualquier error, se hace ROLLBACK para deshacer todos los cambios
        y se retorna el mensaje de error.

        Args:
            id (int): ID del material a eliminar.

        Returns:
            tuple(bool, str | None):
                - (True, None)        si la eliminación fue exitosa.
                - (False, str_error)  si ocurrió un error. `str_error` describe el problema.
        """
        connection = get_connection()
        cursor = connection.cursor()
        try:
            # Paso 1: Eliminar referencias en produccion_materiales
            cursor.execute("DELETE FROM produccion_materiales WHERE material_id=%s", (id,))
            # Paso 2: Eliminar historial de movimientos del material
            cursor.execute("DELETE FROM movimientos_inventario WHERE material_id=%s", (id,))
            # Paso 3: Eliminar el material del catálogo
            cursor.execute("DELETE FROM materiales WHERE id=%s", (id,))
            connection.commit()  # Confirmar todas las eliminaciones
            success = True
            error_msg = None
        except Exception as e:
            connection.rollback()  # Deshacer TODOS los cambios si algo falla
            success = False
            error_msg = str(e)
        finally:
            # `finally` garantiza que siempre se cierra la conexión,
            # incluso si ocurre una excepción.
            cursor.close()
            connection.close()
        return success, error_msg

    @staticmethod
    def get_inventory_report():
        """
        Obtiene los datos del inventario como un DataFrame de pandas.

        Diseñado específicamente para la exportación a Excel. Usa `pd.read_sql`
        para leer directamente la consulta en un DataFrame, que luego se puede
        escribir a un archivo .xlsx con `pd.ExcelWriter`.

        Returns:
            pandas.DataFrame: DataFrame con columnas: id, nombre, stock_actual,
                              stock_minimo, precio_compra.
        """
        import pandas as pd
        connection = get_connection()
        df = pd.read_sql(
            "SELECT id, nombre, stock_actual, stock_minimo, precio_compra FROM materiales",
            connection
        )
        connection.close()
        return df

    @staticmethod
    def get_inventory_list_for_pdf():
        """
        Obtiene la lista de materiales para generar el reporte PDF de inventario.

        Retorna solo los campos necesarios para la tabla del PDF, ordenados
        alfabéticamente por nombre para facilitar la lectura del reporte impreso.

        Returns:
            list[dict]: Lista de materiales con los campos: nombre, stock_actual,
                        stock_minimo, precio_compra.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT nombre, stock_actual, stock_minimo, precio_compra FROM materiales ORDER BY nombre"
        )
        materiales = cursor.fetchall()
        cursor.close()
        connection.close()
        return materiales
