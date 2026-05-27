"""
app/application/services/inventario_service.py - Servicio de Inventario
=========================================================================
Responsabilidad: Contiene la lógica de negocio para la gestión del inventario
de materiales. Coordina las operaciones entre `MaterialRepository` y
`MovimientoRepository`.

Lógica clave - Registro de Movimientos:
    Cuando se registra un movimiento (entrada o salida), este servicio:
    1. Verifica que el material existe.
    2. En caso de "salida", verifica que hay stock suficiente.
    3. Registra el movimiento en `movimientos_inventario` (auditoría).
    4. Actualiza el `stock_actual` en `materiales`.

    IMPORTANTE: Los pasos 3 y 4 deberían ser atómicos (dentro de una
    transacción) para garantizar consistencia. En la implementación actual,
    se realizan en dos consultas separadas. Si el paso 4 falla, el movimiento
    quedaría registrado pero el stock no actualizado (inconsistencia). Para
    producción, se recomienda envolver ambas operaciones en una transacción
    MySQL explícita.

Diferencia con ProduccionService:
    - `InventarioService.registrar_movimiento()`: Movimientos MANUALES que
      realiza el usuario directamente (compras, ajustes de inventario).
    - `ProduccionService.procesar_material()`: Movimientos AUTOMÁTICOS
      generados al asignar materiales a un pedido en producción.
"""
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.movimiento_repository import MovimientoRepository


class InventarioService:
    """
    Servicio de gestión del inventario de materiales.
    """

    @staticmethod
    def get_material_list(stock_status=None, categoria=None):
        """
        Obtiene la lista de materiales con sus filtros y datos complementarios
        necesarios para renderizar la vista de inventario.

        En una sola llamada, retorna los materiales filtrados, el conteo de
        alertas de stock y las categorías disponibles (para los filtros de la UI).

        Args:
            stock_status (str|None): Filtro de estado de stock ("critico", "normal" o None).
            categoria    (str|None): Categoría a filtrar o None para todas.

        Returns:
            tuple(list, dict, list):
                - materiales   (list[dict]): Lista de materiales según los filtros.
                - alerta_stock (dict):       {"bajos": int} con el conteo de materiales críticos.
                - categorias   (list[str]):  Lista de categorías únicas para el selector.
        """
        materiales = MaterialRepository.get_all(stock_status, categoria)
        alerta_stock = MaterialRepository.count_low_stock()
        categorias = MaterialRepository.get_categorias()
        return materiales, alerta_stock, categorias

    @staticmethod
    def get_material(id):
        """
        Obtiene los datos de un material específico por su ID.

        Args:
            id (int): ID del material.

        Returns:
            dict | None: Datos del material o None si no existe.
        """
        return MaterialRepository.get_by_id(id)

    @staticmethod
    def create_material(nombre, categoria, unidad, stock, stock_minimo, costo):
        """
        Crea un nuevo material en el catálogo de inventario.

        No realiza validaciones de negocio adicionales; los campos vienen
        del formulario HTML y se pasan directamente al repositorio.

        Args:
            nombre      (str):   Nombre del material.
            categoria   (str):   Categoría de agrupación.
            unidad      (str):   Unidad de medida.
            stock       (float): Stock inicial.
            stock_minimo(float): Umbral de alerta de stock bajo.
            costo       (float): Costo unitario de compra.

        Returns:
            None.
        """
        MaterialRepository.create(nombre, categoria, unidad, stock, stock_minimo, costo)

    @staticmethod
    def update_material(id, nombre, categoria, unidad, stock_minimo, costo):
        """
        Actualiza los datos de un material existente (excepto el stock_actual).

        El stock_actual NUNCA se modifica directamente desde aquí; solo se
        puede cambiar mediante movimientos de inventario para mantener la
        trazabilidad completa.

        Args:
            id          (int):   ID del material.
            nombre      (str):   Nuevo nombre.
            categoria   (str):   Nueva categoría.
            unidad      (str):   Nueva unidad de medida.
            stock_minimo(float): Nuevo nivel mínimo de alerta.
            costo       (float): Nuevo costo unitario.

        Returns:
            None.
        """
        MaterialRepository.update(id, nombre, categoria, unidad, stock_minimo, costo)

    @staticmethod
    def delete_material(id):
        """
        Elimina un material y todos sus registros relacionados.

        Delega al repositorio, que maneja la eliminación en cascada
        (produccion_materiales -> movimientos_inventario -> materiales).

        Args:
            id (int): ID del material a eliminar.

        Returns:
            tuple(bool, str):
                - (True, "Material eliminado correctamente.") si fue exitoso.
                - (False, "Error al eliminar el material: <detalle>") si falló.
        """
        success, error = MaterialRepository.delete(id)
        if not success:
            return False, f"Error al eliminar el material: {error}"
        return True, "Material eliminado correctamente."

    @staticmethod
    def registrar_movimiento(material_id, tipo, cantidad, motivo):
        """
        Registra un movimiento manual de inventario (entrada o salida) y actualiza el stock.

        Este es el método de negocio más importante de este servicio.
        Aplica las siguientes validaciones ANTES de modificar la base de datos:
        1. Verifica que el material exista.
        2. Si es una "salida", verifica que haya stock suficiente para no quedar en negativo.

        Si las validaciones pasan:
        3. Registra el movimiento en `movimientos_inventario` (auditoría permanente).
        4. Calcula el nuevo stock y lo actualiza en `materiales`.

        Args:
            material_id (int):   ID del material afectado.
            tipo        (str):   Tipo de movimiento: "entrada" o "salida".
            cantidad    (float): Cantidad a agregar o restar del stock.
            motivo      (str):   Descripción del motivo del movimiento.

        Returns:
            tuple(bool, str):
                - (True, "Movimiento registrado exitosamente") si todo fue correcto.
                - (False, "Material no encontrado") si el ID no existe.
                - (False, "No hay suficiente stock") si se intenta una salida mayor al stock.
        """
        # Paso 1: Verificar que el material existe
        material = MaterialRepository.get_by_id(material_id)
        if not material:
            return False, "Material no encontrado"

        # Paso 2: Para salidas, verificar que el stock no quedaría negativo
        if tipo == "salida" and cantidad > float(material["stock_actual"]):
            return False, "No hay suficiente stock"

        # Paso 3: Registrar el movimiento en la tabla de auditoría
        # (sin pedido_id porque es un movimiento manual, no de producción)
        MovimientoRepository.create(material_id, tipo, cantidad, motivo)

        # Paso 4: Calcular y actualizar el nuevo stock
        if tipo == "entrada":
            nuevo_stock = float(material["stock_actual"]) + cantidad
        else:  # tipo == "salida"
            nuevo_stock = float(material["stock_actual"]) - cantidad

        MaterialRepository.update_stock(material_id, nuevo_stock)
        return True, "Movimiento registrado exitosamente"

    @staticmethod
    def get_historial(material_id):
        """
        Obtiene el material y su historial completo de movimientos.

        Prepara todos los datos necesarios para renderizar la vista de
        historial de un material específico.

        Args:
            material_id (int): ID del material.

        Returns:
            tuple(dict|None, list):
                - material    (dict): Datos del material (puede ser None si no existe).
                - movimientos (list): Lista de movimientos ordenados por fecha DESC.
        """
        material = MaterialRepository.get_by_id(material_id)
        movimientos = MovimientoRepository.get_by_material(material_id)
        return material, movimientos
