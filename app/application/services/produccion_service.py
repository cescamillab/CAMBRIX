from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.produccion_repository import ProduccionRepository
from app.infrastructure.repositories.movimiento_repository import MovimientoRepository

class ProduccionService:
    @staticmethod
    def get_produccion_data(pedido_id):
        pedido = PedidoRepository.get_by_id(pedido_id)
        if not pedido:
            return False, "Pedido no encontrado", None, None, 0.0

        if pedido["estado"] == "pendiente":
            PedidoRepository.update_estado(pedido_id, "en_proceso")
            pedido = PedidoRepository.get_by_id(pedido_id)

        materiales = MaterialRepository.get_all()
        usados = ProduccionRepository.get_by_pedido(pedido_id)
        costo_acumulado = ProduccionRepository.get_costo_total_by_pedido(pedido_id)

        return True, pedido, materiales, usados, costo_acumulado

    @staticmethod
    def procesar_material(pedido_id, material_id, cantidad):
        material = MaterialRepository.get_by_id(material_id)
        if not material:
            return False, "Material no encontrado", "danger"

        if cantidad > float(material["stock_actual"]):
            return False, "Stock insuficiente para este material", "danger"

        costo_unitario = float(material["costo_unitario"])
        costo_nuevo = costo_unitario * cantidad

        # Validar que el costo acumulado + el nuevo no supere el valor total del pedido
        pedido = PedidoRepository.get_by_id(pedido_id)
        valor_total = float(pedido["valor_total"])
        costo_acumulado = ProduccionRepository.get_costo_total_by_pedido(pedido_id)

        if costo_acumulado + costo_nuevo > valor_total:
            disponible = valor_total - costo_acumulado
            return False, (
                f"❌ No se puede agregar este material. "
                f"El costo del material (${costo_nuevo:,.2f}) supera el presupuesto disponible (${disponible:,.2f}). "
                f"El costo total de materiales no puede exceder el valor del pedido (${valor_total:,.2f})."
            ), "danger"

        # Registrar producción
        ProduccionRepository.create(pedido_id, material_id, cantidad, costo_unitario, costo_nuevo)

        # Movimiento inventario
        MovimientoRepository.create(material_id, "salida", cantidad, f"Producción Pedido #{pedido_id}", pedido_id)

        # Actualizar stock
        nuevo_stock = float(material["stock_actual"]) - cantidad
        MaterialRepository.update_stock(material_id, nuevo_stock)

        # Alerta de stock bajo
        if nuevo_stock <= float(material["stock_minimo"]):
            return True, f"⚠️ El material '{material['nombre']}' quedó con stock bajo ({nuevo_stock}). Reabastecer pronto.", "warning"

        return True, "Material registrado exitosamente", "success"
