"""
app/infrastructure/repositories/movimiento_repository.py - Repositorio de Movimientos de Inventario
=====================================================================================================
Responsabilidad: Gestiona el registro y consulta del historial de movimientos
de inventario en la tabla `movimientos_inventario`.

Tabla gestionada: `movimientos_inventario`
    Columnas principales: id, material_id, tipo, cantidad, motivo, pedido_id, fecha

¿Para qué sirve esta tabla?
    Es el "libro mayor" del inventario. Cada vez que el stock de un material
    cambia (entra o sale), se registra aquí con la razón del cambio.
    Esto permite responder preguntas como:
    - "¿Cuándo y por qué bajó el stock de 'Madera Pino'?"
    - "¿Qué materiales se usaron en el Pedido #15?"

Tipos de movimiento:
    - "entrada": El stock del material AUMENTA (ej. compra de insumos).
    - "salida":  El stock del material DISMINUYE (ej. uso en producción,
                 mermas, ajustes manuales).

Quién llama a este repositorio:
    - `InventarioService.registrar_movimiento()`: Para entradas/salidas manuales.
    - `ProduccionService.procesar_material()`: Para salidas automáticas al
      asignar materiales a un pedido de producción.
"""
from app.infrastructure.database import get_connection


class MovimientoRepository:
    """
    Clase de repositorio estático para la tabla `movimientos_inventario`.
    """

    @staticmethod
    def create(material_id, tipo, cantidad, motivo, pedido_id=None):
        """
        Registra un nuevo movimiento de inventario en la base de datos.

        Maneja dos casos según si el movimiento está ligado a un pedido o no:
        1. CON pedido_id: Movimiento de producción (salida de material para un pedido).
           Se almacena `pedido_id` para mantener la trazabilidad completa.
        2. SIN pedido_id: Movimiento manual (entrada de compra, ajuste de inventario).
           El campo `pedido_id` queda como NULL en la base de datos.

        NOTA: Este método SOLO registra el movimiento. La actualización del
        `stock_actual` en la tabla `materiales` se hace SEPARADAMENTE en el
        Service correspondiente (InventarioService o ProduccionService).

        Args:
            material_id (int):       ID del material en la tabla `materiales`.
            tipo        (str):       Tipo de movimiento: "entrada" o "salida".
            cantidad    (float):     Cantidad de unidades que entran o salen.
            motivo      (str):       Descripción del motivo del movimiento.
                                     Ej: "Compra proveedor X" o "Producción Pedido #5".
            pedido_id   (int | None): ID del pedido relacionado, si aplica. Default: None.

        Returns:
            None.
        """
        connection = get_connection()
        cursor = connection.cursor()
        if pedido_id:
            # Movimiento de producción: incluir referencia al pedido para trazabilidad
            cursor.execute("""
                INSERT INTO movimientos_inventario
                (material_id, tipo, cantidad, motivo, pedido_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (material_id, tipo, cantidad, motivo, pedido_id))
        else:
            # Movimiento manual: sin referencia a pedido (pedido_id queda NULL)
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
        """
        Obtiene el historial completo de movimientos de un material específico.

        Realiza un JOIN con la tabla `pedidos` para incluir el ID del pedido
        relacionado (si existe) en el resultado, usando LEFT JOIN para no
        excluir los movimientos manuales que no tienen pedido asociado.

        Los resultados se ordenan del más reciente al más antiguo.

        Args:
            material_id (int): ID del material cuyo historial se quiere consultar.

        Returns:
            list[dict]: Lista de movimientos, ordenados por fecha DESC. Cada dict
                        contiene todos los campos de `movimientos_inventario` más
                        `pedido_relacionado` (el ID del pedido si lo hay, o NULL).
        """
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
