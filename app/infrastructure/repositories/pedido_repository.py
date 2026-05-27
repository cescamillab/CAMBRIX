"""
app/infrastructure/repositories/pedido_repository.py - Repositorio de Pedidos
===============================================================================
Responsabilidad: Encapsula TODAS las operaciones de base de datos sobre la
tabla `pedidos` y sus consultas relacionadas. Es el repositorio más extenso
del sistema, con funciones de conteo, suma, filtrado dinámico y reportes.

Tabla gestionada: `pedidos`
    Columnas principales:
        - id:             Identificador único auto-incrementado.
        - cliente_id:     FK a la tabla `clientes`.
        - descripcion:    Descripción del trabajo o servicio a realizar.
        - fecha_creacion: Timestamp de creación automático (CURRENT_TIMESTAMP).
        - fecha_entrega:  Fecha límite de entrega acordada con el cliente.
        - valor_total:    Precio total pactado con el cliente.
        - anticipo:       Monto adelantado por el cliente. El saldo es valor_total - anticipo.
        - estado:         Estado actual del pedido ("pendiente", "en_proceso", "terminado").
        - responsable_id: FK a `usuarios` (el empleado asignado al pedido).

Lógica de doble perspectiva (Jefe vs Empleado):
    Muchos métodos tienen dos versiones:
    - La versión normal (ej. count_total()) opera sobre TODOS los pedidos.
    - La versión "_for_user" (ej. count_total_for_user(user_id)) filtra
      por `responsable_id = user_id`, mostrando solo los pedidos del empleado.
    Esto permite que el Dashboard y la lista de pedidos sean personalizados
    según el rol del usuario autenticado.
"""
from app.infrastructure.database import get_connection
import pandas as pd


class PedidoRepository:
    """
    Clase de repositorio estático para la tabla `pedidos`.
    """

    # ===========================================================================
    # MÉTODOS DE CONTEO Y AGREGACIÓN (para KPIs del Dashboard - Vista JEFE)
    # ===========================================================================

    @staticmethod
    def count_total():
        """
        Cuenta el número total de pedidos en el sistema (todos los estados).

        Returns:
            int: Total de pedidos. Retorna 0 si la tabla está vacía.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM pedidos")
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] if res else 0

    @staticmethod
    def count_by_status(status):
        """
        Cuenta los pedidos que tienen un estado específico.

        Args:
            status (str): Estado a contar. Ej: "pendiente", "en_proceso", "terminado".

        Returns:
            int: Número de pedidos en ese estado.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) AS count FROM pedidos WHERE estado = %s", (status,)
        )
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["count"] if res else 0

    @staticmethod
    def sum_total_invoiced():
        """
        Suma el `valor_total` de todos los pedidos (total facturado acumulado).

        Es el KPI "Total Facturado" que aparece en el Dashboard del jefe.

        Returns:
            float: Suma total del valor de todos los pedidos. Retorna 0 si no hay pedidos.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT SUM(valor_total) AS total FROM pedidos")
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def sum_total_pending_balance():
        """
        Calcula el saldo pendiente total de todos los pedidos.

        Fórmula: SUM(valor_total - anticipo)
        Representa el dinero que los clientes aún deben pagar a la empresa.

        Returns:
            float: Total del saldo pendiente de cobro en todos los pedidos.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT SUM(valor_total - anticipo) AS total FROM pedidos")
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def group_by_status():
        """
        Agrupa y cuenta los pedidos por estado para el gráfico de torta del Dashboard.

        Returns:
            list[dict]: Lista de dicts, cada uno con "estado" y "total".
                        Ej: [{"estado": "pendiente", "total": 5}, ...]
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT estado, COUNT(*) as total FROM pedidos GROUP BY estado")
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_monthly_income():
        """
        Agrupa el valor total de pedidos por mes para el gráfico de barras del Dashboard.

        Usa `DATE_FORMAT` de MySQL para formatear la fecha como 'YYYY-MM', lo que
        permite agrupar todos los pedidos del mismo mes independientemente del día.

        Returns:
            list[dict]: Lista de dicts con "mes" (str 'YYYY-MM') y "total_mes" (float).
                        Ordenados cronológicamente.
        """
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

    # ===========================================================================
    # MÉTODOS DE CONTEO Y AGREGACIÓN (para KPIs del Dashboard - Vista EMPLEADO)
    # Misma lógica pero filtrada por responsable_id = user_id
    # ===========================================================================

    @staticmethod
    def count_total_for_user(user_id):
        """Cuenta el total de pedidos asignados a un empleado específico."""
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) AS total FROM pedidos WHERE responsable_id = %s", (user_id,)
        )
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] if res else 0

    @staticmethod
    def count_by_status_for_user(user_id, status):
        """Cuenta los pedidos de un empleado filtrados por estado."""
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) AS count FROM pedidos WHERE responsable_id = %s AND estado = %s",
            (user_id, status)
        )
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["count"] if res else 0

    @staticmethod
    def sum_total_invoiced_for_user(user_id):
        """Suma el valor total de los pedidos de un empleado específico."""
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT SUM(valor_total) AS total FROM pedidos WHERE responsable_id = %s", (user_id,)
        )
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def sum_total_pending_balance_for_user(user_id):
        """Calcula el saldo pendiente de los pedidos asignados a un empleado."""
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT SUM(valor_total - anticipo) AS total FROM pedidos WHERE responsable_id = %s",
            (user_id,)
        )
        res = cursor.fetchone()
        cursor.close()
        connection.close()
        return res["total"] or 0

    @staticmethod
    def group_by_status_for_user(user_id):
        """Agrupa los pedidos de un empleado por estado para su gráfico en el Dashboard."""
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT estado, COUNT(*) as total FROM pedidos WHERE responsable_id = %s GROUP BY estado",
            (user_id,)
        )
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def get_monthly_income_for_user(user_id):
        """Obtiene los ingresos mensuales de los pedidos de un empleado específico."""
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

    # ===========================================================================
    # CONSULTAS ANALÍTICAS (para widgets del Dashboard - Solo Jefe)
    # ===========================================================================

    @staticmethod
    def get_top_clientes():
        """
        Obtiene los 5 clientes que más han facturado históricamente.

        Realiza un JOIN con `clientes` para obtener el nombre, agrupa por
        cliente y suma el valor total de sus pedidos.

        Returns:
            list[dict]: Los 5 clientes con mayor valor total, con campos:
                        "nombre" y "total_facturado". Ordenados DESC.
        """
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
        """
        Obtiene los 5 pedidos más recientes de todo el sistema (para el jefe).

        Incluye el nombre del cliente mediante JOIN con `clientes`.

        Returns:
            list[dict]: Los 5 pedidos más recientes con campos:
                        id, cliente (nombre), valor_total, estado.
        """
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
        """
        Obtiene los 5 pedidos más recientes asignados a un empleado específico.

        Args:
            user_id (int): ID del empleado autenticado.

        Returns:
            list[dict]: Los 5 pedidos más recientes del empleado.
        """
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

    # ===========================================================================
    # CRUD PRINCIPAL
    # ===========================================================================

    @staticmethod
    def filter_pedidos(role, user_id, busqueda, estado, responsable,
                       fecha_inicio=None, fecha_fin=None, orden_id=None, orden_fecha=None):
        """
        Obtiene la lista de pedidos con filtros dinámicos y ordenamiento.

        Esta es la consulta más compleja de la aplicación. Construye un
        SQL dinámicamente según los parámetros de filtro y ordenamiento
        recibidos desde el formulario de búsqueda de la vista de pedidos.

        Lógica de acceso por rol:
        - "jefe": Ve TODOS los pedidos de todos los empleados. Puede filtrar
                  por responsable específico.
        - "empleado": Solo ve sus propios pedidos (filtro forzado por responsable_id).

        Filtros aplicables:
        - busqueda:    Búsqueda parcial (LIKE) en el nombre del cliente.
        - estado:      Filtro exacto por estado del pedido.
        - responsable: (Solo jefe) Filtro por empleado responsable.
        - fecha_inicio/fecha_fin: Rango de fechas de entrega.

        Ordenamiento:
        - orden_id:    Ordena por ID del pedido ("asc" o "desc").
        - orden_fecha: Ordena por fecha de entrega ("asc" o "desc").
        - Si no se especifica ordenamiento, por defecto ordena por fecha_creacion DESC.

        Args:
            role       (str):       Rol del usuario autenticado ("jefe" o "empleado").
            user_id    (int):       ID del usuario autenticado.
            busqueda   (str):       Término de búsqueda por nombre de cliente.
            estado     (str):       Estado a filtrar (vacío = todos).
            responsable(str):       ID del responsable a filtrar (vacío = todos).
            fecha_inicio(str|None): Fecha inicio en formato 'YYYY-MM-DD'.
            fecha_fin  (str|None):  Fecha fin en formato 'YYYY-MM-DD'.
            orden_id   (str|None):  Dirección de orden por ID: "asc" o "desc".
            orden_fecha(str|None):  Dirección de orden por fecha: "asc" o "desc".

        Returns:
            list[dict]: Lista de pedidos que cumplen todos los filtros, incluyendo
                        cliente_nombre, responsable_nombre y saldo (valor_total - anticipo).
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        # Consulta base con JOINs para obtener nombres de cliente y responsable,
        # y el saldo calculado como campo virtual.
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

        # Restricción de rol: los empleados solo ven sus propios pedidos
        if role != "jefe":
            query += " AND pedidos.responsable_id = %s"
            params.append(user_id)

        # Filtro de búsqueda por nombre de cliente (búsqueda parcial)
        if busqueda:
            query += " AND clientes.nombre LIKE %s"
            params.append(f"%{busqueda}%")

        # Filtro de estado exacto
        if estado:
            query += " AND pedidos.estado = %s"
            params.append(estado)

        # Filtro por responsable (solo disponible para el jefe)
        if responsable and role == "jefe":
            query += " AND pedidos.responsable_id = %s"
            params.append(responsable)

        # Filtro de rango de fechas de entrega
        if fecha_inicio:
            query += " AND pedidos.fecha_entrega >= %s"
            params.append(f"{fecha_inicio} 00:00:00")
        if fecha_fin:
            query += " AND pedidos.fecha_entrega <= %s"
            params.append(f"{fecha_fin} 23:59:59")

        # Construcción del ORDER BY dinámico
        order_clauses = []
        if orden_id in ['asc', 'desc']:
            order_clauses.append(f"pedidos.id {orden_id.upper()}")
        if orden_fecha in ['asc', 'desc']:
            order_clauses.append(f"pedidos.fecha_entrega {orden_fecha.upper()}")

        if order_clauses:
            query += " ORDER BY " + ", ".join(order_clauses)
        else:
            # Orden por defecto: más recientes primero
            query += " ORDER BY pedidos.fecha_creacion DESC"

        cursor.execute(query, params)
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    @staticmethod
    def create(cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        """
        Inserta un nuevo pedido en la base de datos.

        El estado inicial es siempre "pendiente" (valor por defecto en la DB).
        La `fecha_creacion` es asignada automáticamente por MySQL (CURRENT_TIMESTAMP).

        Args:
            cliente_id    (int):  ID del cliente (debe existir en la tabla `clientes`).
            descripcion   (str):  Descripción detallada del trabajo a realizar.
            fecha_entrega (str):  Fecha límite en formato 'YYYY-MM-DD'.
            valor_total   (float): Precio total acordado con el cliente.
            anticipo      (float): Monto adelantado. Puede ser 0.
            responsable_id(int):  ID del empleado asignado al pedido.

        Returns:
            int: El ID auto-generado del nuevo pedido.
        """
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
        """
        Obtiene los datos básicos de un pedido por su ID (solo la tabla `pedidos`).

        A diferencia de `get_detail_by_id`, esta consulta no hace JOINs y
        retorna solo los campos propios de la tabla. Usada en validaciones
        de negocio donde solo se necesita verificar el estado o el responsable.

        Args:
            pedido_id (int): ID del pedido a buscar.

        Returns:
            dict | None: Datos del pedido o None si no existe.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
        pedido = cursor.fetchone()
        cursor.close()
        connection.close()
        return pedido

    @staticmethod
    def get_detail_by_id(pedido_id):
        """
        Obtiene los datos completos y enriquecidos de un pedido (con JOINs).

        Diseñado para la vista de detalle del pedido. Incluye información
        del cliente (nombre, teléfono, correo), del responsable y el saldo
        calculado, evitando múltiples consultas desde el servicio.

        Args:
            pedido_id (int): ID del pedido a consultar.

        Returns:
            dict | None: Diccionario enriquecido con los campos de pedidos más:
                         cliente_nombre, telefono, correo, responsable_nombre, saldo.
                         Retorna None si el pedido no existe.
        """
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
        """
        Actualiza ÚNICAMENTE el campo `estado` de un pedido.

        Método de propósito único para cambios de estado. La lógica de
        validación (ej. no permitir cambiar un pedido "terminado") se
        maneja en `PedidoService.actualizar_estado()` antes de llegar aquí.

        Args:
            pedido_id   (int): ID del pedido a actualizar.
            nuevo_estado(str): Nuevo estado a asignar.

        Returns:
            None.
        """
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, pedido_id)
        )
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def update(pedido_id, cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        """
        Actualiza todos los campos editables de un pedido existente.

        Args:
            pedido_id    (int):   ID del pedido a actualizar.
            cliente_id   (int):   Nuevo ID de cliente.
            descripcion  (str):   Nueva descripción del trabajo.
            fecha_entrega(str):   Nueva fecha límite 'YYYY-MM-DD'.
            valor_total  (float): Nuevo valor total acordado.
            anticipo     (float): Nuevo monto de anticipo.
            responsable_id(int):  Nuevo ID del responsable.

        Returns:
            None.
        """
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
        """
        Elimina permanentemente un pedido de la base de datos.

        Args:
            pedido_id (int): ID del pedido a eliminar.

        Returns:
            None.
        """
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
        connection.commit()
        cursor.close()
        connection.close()

    # ===========================================================================
    # HELPERS Y MÉTODOS DE REPORTE
    # ===========================================================================

    @staticmethod
    def get_report_query(base_query, date_col, fecha_inicio, fecha_fin):
        """
        Función auxiliar que agrega cláusulas WHERE de rango de fechas a una consulta.

        Diseñada para reutilización en los métodos de reporte. Detecta si la
        consulta base ya tiene un WHERE para usar AND en lugar de WHERE.

        Args:
            base_query  (str): La consulta SQL base sin filtros de fecha.
            date_col    (str): Nombre de la columna de fecha a filtrar
                               (ej. "fecha_creacion" o "pedidos.fecha_creacion").
            fecha_inicio(str | None): Fecha inicio 'YYYY-MM-DD' o None.
            fecha_fin   (str | None): Fecha fin 'YYYY-MM-DD' o None.

        Returns:
            tuple(str, tuple): La consulta con los filtros añadidos y la tupla
                               de parámetros para el cursor.execute().
        """
        params = []
        # Detectar si ya existe una cláusula WHERE en la consulta base
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
        """
        Obtiene todos los pedidos en un rango de fechas como DataFrame de pandas.

        Usa `pd.read_sql` para una lectura eficiente directa a DataFrame,
        que luego `ReporteService` escribe a un archivo .xlsx.

        Args:
            fecha_inicio (str | None): Fecha inicio del rango.
            fecha_fin    (str | None): Fecha fin del rango.

        Returns:
            pandas.DataFrame: Todos los campos de `pedidos` en el rango dado.
        """
        connection = get_connection()
        query, params = PedidoRepository.get_report_query(
            "SELECT * FROM pedidos", "fecha_creacion", fecha_inicio, fecha_fin
        )
        df = pd.read_sql(query, connection, params=params)
        connection.close()
        return df

    @staticmethod
    def get_pedidos_report_pdf(fecha_inicio, fecha_fin):
        """
        Obtiene los pedidos para el reporte PDF, con datos del cliente incluidos.

        A diferencia del reporte Excel (que usa todos los campos de `pedidos`),
        el PDF usa solo los campos necesarios para la tabla impresa.

        Args:
            fecha_inicio (str | None): Fecha inicio del rango.
            fecha_fin    (str | None): Fecha fin del rango.

        Returns:
            list[dict]: Lista de pedidos con campos: id, cliente, estado,
                        fecha_creacion, valor_total.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        base_query = """
            SELECT pedidos.id, clientes.nombre AS cliente, pedidos.estado,
                   pedidos.fecha_creacion, pedidos.valor_total
            FROM pedidos
            JOIN clientes ON pedidos.cliente_id = clientes.id
        """
        query, params = PedidoRepository.get_report_query(
            base_query, "pedidos.fecha_creacion", fecha_inicio, fecha_fin
        )
        cursor.execute(query, params)
        pedidos = cursor.fetchall()
        cursor.close()
        connection.close()
        return pedidos
