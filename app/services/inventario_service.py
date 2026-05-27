from app.models.material_model import MaterialModel
from app.models.movimiento_model import MovimientoModel

class InventarioService:
    @staticmethod
    def get_material_list(stock_status=None, categoria=None):
        materiales = MaterialModel.get_all(stock_status, categoria)
        alerta_stock = MaterialModel.count_low_stock()
        categorias = MaterialModel.get_categorias()
        return materiales, alerta_stock, categorias

    @staticmethod
    def get_material(id):
        return MaterialModel.get_by_id(id)

    @staticmethod
    def create_material(nombre, categoria, unidad, stock, stock_minimo, costo):
        MaterialModel.create(nombre, categoria, unidad, stock, stock_minimo, costo)

    @staticmethod
    def update_material(id, nombre, categoria, unidad, stock_minimo, costo):
        MaterialModel.update(id, nombre, categoria, unidad, stock_minimo, costo)

    @staticmethod
    def delete_material(id):
        success, error = MaterialModel.delete(id)
        if not success:
            return False, f"Error al eliminar el material: {error}"
        return True, "Material eliminado correctamente."

    @staticmethod
    def registrar_movimiento(material_id, tipo, cantidad, motivo):
        material = MaterialModel.get_by_id(material_id)
        if not material:
            return False, "Material no encontrado"

        if tipo == "salida" and cantidad > float(material["stock_actual"]):
            return False, "No hay suficiente stock"

        # Insertar movimiento
        MovimientoModel.create(material_id, tipo, cantidad, motivo)

        # Actualizar stock
        if tipo == "entrada":
            nuevo_stock = float(material["stock_actual"]) + cantidad
        else:
            nuevo_stock = float(material["stock_actual"]) - cantidad

        MaterialModel.update_stock(material_id, nuevo_stock)
        return True, "Movimiento registrado exitosamente"

    @staticmethod
    def get_historial(material_id):
        material = MaterialModel.get_by_id(material_id)
        movimientos = MovimientoModel.get_by_material(material_id)
        return material, movimientos
