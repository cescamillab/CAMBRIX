"""
app/infrastructure/repositories/produccion_repository.py - Repositorio de Producción
======================================================================================
Responsabilidad: Gestiona todas las operaciones sobre la tabla
`produccion_materiales`, que es la tabla de trazabilidad central del sistema.

Tabla gestionada: `produccion_materiales`
    Columnas principales:
        - id:             ID auto-incrementado del registro.
        - pedido_id:      FK a `pedidos`. El pedido al que se destinó el material.
        - material_id:    FK a `materiales`. El material consumido.
        - cantidad_usada: Cantidad de unidades del material utilizadas.
        - costo_unitario: Costo del material al momento de la asignación (snapshot).
        - costo_total:    cantidad_usada * costo_unitario (cálculo pre-computado).

¿Por qué almacenar `costo_unitario` en lugar de calcularlo dinámicamente?
    El precio de un material puede cambiar con el tiempo. Al registrar el
    costo_unitario en el momento exacto de la asignación, se garantiza que
    los reportes de rentabilidad reflejen el costo REAL que tuvo ese pedido,
    sin importar cambios futuros en el precio del material. Es un "snapshot"
    histórico del precio.

Relación Many-to-Many:
    Esta tabla implementa la relación muchos-a-muchos entre `pedidos` y
    `materiales`: un pedido puede usar muchos materiales, y un mismo
    material puede ser usado en muchos pedidos.
"""
from app.infrastructure.database import get_connection
import pandas as pd


class ProduccionRepository:
    """
    Clase de repositorio estático para la tabla `produccion_materiales`.
    """

    @staticmethod
    def get_costo_total_by_pedido(pedido_id):
        """
        Calcula el costo acumulado total de materiales ya asignados a un pedido.

        Usa COALESCE para retornar 0.0 si no hay registros (cuando SUM es NULL).
        Este valor se usa en `ProduccionService` para validar que el costo
        de materiales no exceda el valor total del pedido.

        Args:
            pedido_id (int): ID del pedido.

        Returns:
            float: Suma de todos los `costo_total` de materiales del pedido.
                   Retorna 0.0 si no se han asignado materiales aún.
        """
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
        """
        Obtiene todos los materiales que han sido asignados a un pedido.

        Realiza un JOIN con `materiales` para incluir el nombre del material
        en cada registro, facilitando la visualización en la vista de
        gestión de producción.

        Args:
            pedido_id (int): ID del pedido del que se quieren los materiales.

        Returns:
            list[dict]: Lista de registros de produccion_materiales, cada uno
                        con los campos propios más `nombre` (del material).
        """
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
        """
        Registra el uso de un material en la producción de un pedido.

        Este registro es permanente y no debe editarse. Representa un hecho
        histórico: "X unidades del material Y fueron usadas en el pedido Z,
        a un costo de W por unidad".

        Args:
            pedido_id     (int):   ID del pedido que consume el material.
            material_id   (int):   ID del material consumido.
            cantidad_usada(float): Cantidad de unidades utilizadas.
            costo_unitario(float): Precio unitario del material en ese momento.
            costo_total   (float): cantidad_usada * costo_unitario (ya calculado
                                   en ProduccionService antes de llamar aquí).

        Returns:
            None.
        """
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
        """
        Obtiene los 5 materiales más utilizados en producción (por cantidad total).

        Agrupa los registros por `material_id`, suma las cantidades usadas y
        ordena de mayor a menor. Usado en el widget "Top Materiales" del Dashboard.

        Returns:
            list[dict]: Los 5 materiales más usados con campos:
                        "nombre" y "total_usado" (suma de cantidades).
        """
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
        """
        Función auxiliar para agregar filtros de fecha a una consulta de reporte.

        Idéntica en lógica a `PedidoRepository.get_report_query()`. Se duplica
        aquí para que el repositorio sea autocontenido y no dependa de otro
        repositorio (principio de independencia de módulos).

        Args:
            base_query  (str):       Consulta SQL base.
            date_col    (str):       Columna de fecha a filtrar.
            fecha_inicio(str | None): Fecha inicio 'YYYY-MM-DD'.
            fecha_fin   (str | None): Fecha fin 'YYYY-MM-DD'.

        Returns:
            tuple(str, tuple): Query modificada y parámetros.
        """
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
        """
        Obtiene los datos de producción como DataFrame de pandas para exportar a Excel.

        Combina datos de `produccion_materiales`, `materiales` y `pedidos`
        mediante JOINs para generar un reporte completo con todos los campos
        relevantes de cada movimiento de producción.

        Args:
            fecha_inicio (str | None): Fecha inicio del rango (basada en fecha del pedido).
            fecha_fin    (str | None): Fecha fin del rango.

        Returns:
            pandas.DataFrame: DataFrame con columnas: id, pedido_id, material,
                              cantidad_usada, costo_unitario, costo_total, fecha_creacion.
        """
        connection = get_connection()
        base_query = """
        SELECT pm.id, pm.pedido_id, m.nombre AS material, pm.cantidad_usada,
               pm.costo_unitario, pm.costo_total, p.fecha_creacion
        FROM produccion_materiales pm
        JOIN materiales m ON pm.material_id = m.id
        JOIN pedidos p ON pm.pedido_id = p.id
        """
        query, params = ProduccionRepository.get_report_query(
            base_query, "p.fecha_creacion", fecha_inicio, fecha_fin
        )
        df = pd.read_sql(query, connection, params=params)
        connection.close()
        return df

    @staticmethod
    def get_produccion_report_pdf(fecha_inicio, fecha_fin):
        """
        Obtiene los datos de producción para el reporte PDF.

        Similar a `get_produccion_report_excel` pero retorna una lista de
        diccionarios (no DataFrame) con solo los campos necesarios para
        la tabla del reporte PDF impreso.

        Args:
            fecha_inicio (str | None): Fecha inicio del rango.
            fecha_fin    (str | None): Fecha fin del rango.

        Returns:
            list[dict]: Lista de registros con campos: pedido_id, material,
                        cantidad_usada, costo_total, fecha_creacion.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        base_query = """
        SELECT pm.pedido_id, m.nombre AS material, pm.cantidad_usada,
               pm.costo_total, p.fecha_creacion
        FROM produccion_materiales pm
        JOIN materiales m ON pm.material_id = m.id
        JOIN pedidos p ON pm.pedido_id = p.id
        """
        query, params = ProduccionRepository.get_report_query(
            base_query, "p.fecha_creacion", fecha_inicio, fecha_fin
        )
        cursor.execute(query, params)
        registros = cursor.fetchall()
        cursor.close()
        connection.close()
        return registros
