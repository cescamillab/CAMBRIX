from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.movimiento_repository import MovimientoRepository

class InventarioService:
    @staticmethod
    def get_material_list(stock_status=None, categoria=None):
        materiales = MaterialRepository.get_all(stock_status, categoria)
        alerta_stock = MaterialRepository.count_low_stock()
        categorias = MaterialRepository.get_categorias()
        return materiales, alerta_stock, categorias

    @staticmethod
    def get_material(id):
        return MaterialRepository.get_by_id(id)

    @staticmethod
    def create_material(nombre, categoria, unidad, stock, stock_minimo, costo):
        MaterialRepository.create(nombre, categoria, unidad, stock, stock_minimo, costo)

    @staticmethod
    def update_material(id, nombre, categoria, unidad, stock_minimo, costo):
        MaterialRepository.update(id, nombre, categoria, unidad, stock_minimo, costo)

    @staticmethod
    def delete_material(id):
        success, error = MaterialRepository.delete(id)
        if not success:
            return False, f"Error al eliminar el material: {error}"
        return True, "Material eliminado correctamente."

    @staticmethod
    def registrar_movimiento(material_id, tipo, cantidad, motivo):
        material = MaterialRepository.get_by_id(material_id)
        if not material:
            return False, "Material no encontrado"

        if tipo == "salida" and cantidad > float(material["stock_actual"]):
            return False, "No hay suficiente stock"

        # Insertar movimiento
        MovimientoRepository.create(material_id, tipo, cantidad, motivo)

        # Actualizar stock
        if tipo == "entrada":
            nuevo_stock = float(material["stock_actual"]) + cantidad
        else:
            nuevo_stock = float(material["stock_actual"]) - cantidad

        MaterialRepository.update_stock(material_id, nuevo_stock)
        return True, "Movimiento registrado exitosamente"

    @staticmethod
    def get_historial(material_id):
        material = MaterialRepository.get_by_id(material_id)
        movimientos = MovimientoRepository.get_by_material(material_id)
        return material, movimientos
