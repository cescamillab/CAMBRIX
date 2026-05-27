from app.models.pedido_model import PedidoModel
from app.models.cliente_model import ClienteModel
from app.models.usuario_model import UsuarioModel

class PedidoService:
    @staticmethod
    def get_filtered(role, user_id, busqueda, estado, responsable, fecha_inicio=None, fecha_fin=None, orden_id=None, orden_fecha=None):
        pedidos = PedidoModel.filter_pedidos(role, user_id, busqueda, estado, responsable, fecha_inicio, fecha_fin, orden_id, orden_fecha)
        empleados = []
        if role == "jefe":
            empleados = UsuarioModel.get_by_role("empleado")
        return pedidos, empleados

    @staticmethod
    def get_create_data():
        clientes = ClienteModel.get_all()
        empleados = UsuarioModel.get_by_role("empleado")
        return clientes, empleados

    @staticmethod
    def create_pedido(tipo_cliente, cliente_existente, nombre, telefono, correo, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        if tipo_cliente == "existente":
            cliente_id = cliente_existente
        else:
            cliente_id = ClienteModel.create(nombre, telefono, correo)

        return PedidoModel.create(cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)

    @staticmethod
    def actualizar_estado(pedido_id, nuevo_estado, rol, user_id):
        pedido = PedidoModel.get_by_id(pedido_id)
        if not pedido:
            return False, "Pedido no encontrado", 404
        
        if pedido["estado"] == "terminado":
            return False, "El pedido ya está terminado", 400
            
        if rol == "empleado" and pedido["responsable_id"] != user_id:
            return False, "Acceso denegado", 403
            
        PedidoModel.update_estado(pedido_id, nuevo_estado)
        return True, "Estado actualizado", 200

    @staticmethod
    def get_detail(pedido_id, rol, user_id):
        from app.models.produccion_model import ProduccionModel
        
        pedido = PedidoModel.get_detail_by_id(pedido_id)
        if not pedido:
            return False, None, None, 404
            
        if rol == "empleado" and pedido["responsable_id"] != user_id:
            return False, None, None, 403
            
        produccion = ProduccionModel.get_by_pedido(pedido_id)
        return True, pedido, produccion, 200

    @staticmethod
    def get_edit_data(pedido_id):
        pedido = PedidoModel.get_by_id(pedido_id)
        if not pedido:
            return False, None, None, None, 404
            
        if pedido["estado"] == "terminado":
            return False, None, None, None, 400
            
        clientes = ClienteModel.get_all()
        empleados = UsuarioModel.get_by_role("empleado")
        
        return True, pedido, clientes, empleados, 200

    @staticmethod
    def update_pedido(pedido_id, cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        PedidoModel.update(pedido_id, cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)
        return True

    @staticmethod
    def delete_pedido(pedido_id):
        PedidoModel.delete(pedido_id)
        return True
