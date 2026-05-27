"""
app/application/services/produccion_service.py - Servicio de Producción
=========================================================================
Responsabilidad: Contiene la lógica de negocio más crítica del sistema:
el registro del consumo de materiales en la producción de un pedido.
Coordina cuatro repositorios en una sola operación atómica lógica.

¿Qué es "gestionar producción"?
    Es el proceso de registrar qué materiales se usaron para fabricar o
    completar un pedido. Por ejemplo: "Para el Pedido #15 (silla de madera),
    se usaron 2 metros de Madera Pino y 4 tornillos de 1/2 pulgada".

Flujo del método `procesar_material()`:
    1. Verificar que el material existe en el catálogo.
    2. Verificar que hay stock suficiente del material.
    3. Calcular el costo del uso (cantidad * costo_unitario).
    4. Verificar que el costo total acumulado + este nuevo costo NO supere
       el valor total del pedido (control de presupuesto).
    5. Registrar el uso en `produccion_materiales` (trazabilidad).
    6. Registrar el movimiento en `movimientos_inventario` (auditoría).
    7. Actualizar el `stock_actual` del material en `materiales`.
    8. Verificar si el nuevo stock quedó en zona crítica y alertar.

Control de Presupuesto (Paso 4 - Lógica Crítica):
    El sistema no permite que el costo de los materiales supere el valor
    del pedido. Esto sirve como guardia contra el uso excesivo de insumos
    que haría que el pedido no sea rentable o incluso genere pérdidas.

    Fórmula:
        costo_acumulado_anterior + costo_nuevo_material <= valor_total_pedido

    Si se excede, se rechaza la operación con un mensaje descriptivo que
    indica el presupuesto disponible restante.

Auto-transición de Estado:
    Cuando se accede a gestionar la producción de un pedido que aún está
    en estado "pendiente", el sistema automáticamente lo cambia a "en_proceso".
    Esto refleja la realidad del flujo de trabajo: si ya se están usando
    materiales, el pedido está en proceso.
"""
from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.produccion_repository import ProduccionRepository
from app.infrastructure.repositories.movimiento_repository import MovimientoRepository


class ProduccionService:
    """
    Servicio de lógica de negocio para la gestión de producción de pedidos.
    """

    @staticmethod
    def get_produccion_data(pedido_id):
        """
        Obtiene todos los datos necesarios para renderizar la vista de gestión de producción.

        Además de recopilar datos, aplica la auto-transición de estado:
        si el pedido está "pendiente", lo pasa a "en_proceso" automáticamente
        al ingresar a la vista de producción.

        Args:
            pedido_id (int): ID del pedido cuya producción se va a gestionar.

        Returns:
            tuple(bool, str|dict, list|None, list|None, float):
                En éxito:
                    (True, pedido_dict, materiales_list, usados_list, costo_acumulado_float)
                En fallo (pedido no encontrado):
                    (False, "Pedido no encontrado", None, None, 0.0)

            Donde:
                - pedido_dict:        Datos del pedido.
                - materiales_list:    Todos los materiales disponibles (para el selector).
                - usados_list:        Materiales ya asignados a este pedido.
                - costo_acumulado_float: Suma del costo de materiales ya asignados.
        """
        pedido = PedidoRepository.get_by_id(pedido_id)
        if not pedido:
            return False, "Pedido no encontrado", None, None, 0.0

        # Auto-transición: si el pedido está pendiente, iniciarlo automáticamente
        # al momento en que se comienza a registrar producción
        if pedido["estado"] == "pendiente":
            PedidoRepository.update_estado(pedido_id, "en_proceso")
            # Recargar el pedido para tener el estado actualizado en la vista
            pedido = PedidoRepository.get_by_id(pedido_id)

        materiales = MaterialRepository.get_all()
        usados = ProduccionRepository.get_by_pedido(pedido_id)
        costo_acumulado = ProduccionRepository.get_costo_total_by_pedido(pedido_id)

        return True, pedido, materiales, usados, costo_acumulado

    @staticmethod
    def procesar_material(pedido_id, material_id, cantidad):
        """
        Registra el uso de un material en la producción de un pedido.

        Esta es la operación de negocio más importante del sistema.
        Coordina 4 repositorios y aplica múltiples validaciones.

        Validaciones (en orden de verificación):
        1. El material debe existir en el catálogo.
        2. La cantidad solicitada no debe superar el stock disponible.
        3. El costo de este uso + los costos anteriores no deben superar
           el valor total del pedido (control de presupuesto).

        Si todas las validaciones pasan, realiza 3 escrituras en la DB:
        A. INSERT en `produccion_materiales` (trazabilidad del pedido).
        B. INSERT en `movimientos_inventario` (auditoría del inventario).
        C. UPDATE en `materiales` (actualización del stock_actual).

        Args:
            pedido_id   (int):   ID del pedido que consume el material.
            material_id (str):   ID del material (viene como string del formulario HTML).
            cantidad    (float): Cantidad de unidades a consumir.

        Returns:
            tuple(bool, str, str): (éxito, mensaje_para_usuario, tipo_flash)
                Donde tipo_flash es: "success", "warning" o "danger".

                Casos de retorno:
                - (False, "Material no encontrado", "danger"): ID inválido.
                - (False, "Stock insuficiente...", "danger"): Sin stock.
                - (False, "❌ No se puede agregar... presupuesto", "danger"): Excede presupuesto.
                - (True, "⚠️ Stock bajo...", "warning"): Éxito pero stock crítico.
                - (True, "Material registrado exitosamente", "success"): Éxito normal.
        """
        # Validación 1: El material debe existir
        material = MaterialRepository.get_by_id(material_id)
        if not material:
            return False, "Material no encontrado", "danger"

        # Validación 2: Stock suficiente
        if cantidad > float(material["stock_actual"]):
            return False, "Stock insuficiente para este material", "danger"

        # Calcular el costo de este uso específico
        costo_unitario = float(material["costo_unitario"])
        costo_nuevo = costo_unitario * cantidad

        # Validación 3: Control de presupuesto del pedido
        pedido = PedidoRepository.get_by_id(pedido_id)
        valor_total = float(pedido["valor_total"])
        costo_acumulado = ProduccionRepository.get_costo_total_by_pedido(pedido_id)

        if costo_acumulado + costo_nuevo > valor_total:
            # Calcular cuánto presupuesto queda disponible para informar al usuario
            disponible = valor_total - costo_acumulado
            return False, (
                f"❌ No se puede agregar este material. "
                f"El costo del material (${costo_nuevo:,.2f}) supera el presupuesto disponible (${disponible:,.2f}). "
                f"El costo total de materiales no puede exceder el valor del pedido (${valor_total:,.2f})."
            ), "danger"

        # -----------------------------------------------------------------------
        # Todas las validaciones pasaron: Ejecutar las 3 escrituras en la DB
        # -----------------------------------------------------------------------

        # A. Registrar en la tabla de trazabilidad de producción
        ProduccionRepository.create(pedido_id, material_id, cantidad, costo_unitario, costo_nuevo)

        # B. Registrar en el historial de movimientos de inventario
        # Se incluye pedido_id para poder rastrear de qué pedido provino la salida
        MovimientoRepository.create(
            material_id, "salida", cantidad,
            f"Producción Pedido #{pedido_id}", pedido_id
        )

        # C. Actualizar el stock actual del material
        nuevo_stock = float(material["stock_actual"]) - cantidad
        MaterialRepository.update_stock(material_id, nuevo_stock)

        # Verificar si el stock quedó en zona crítica y advertir al usuario
        if nuevo_stock <= float(material["stock_minimo"]):
            return True, (
                f"⚠️ El material '{material['nombre']}' quedó con stock bajo ({nuevo_stock}). "
                f"Reabastecer pronto."
            ), "warning"

        # Todo bien, sin alertas de stock
        return True, "Material registrado exitosamente", "success"
