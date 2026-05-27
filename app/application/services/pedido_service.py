from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.cliente_repository import ClienteRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

class PedidoService:
    @staticmethod
    def get_filtered(role, user_id, busqueda, estado, responsable, fecha_inicio=None, fecha_fin=None, orden_id=None, orden_fecha=None):
        pedidos = PedidoRepository.filter_pedidos(role, user_id, busqueda, estado, responsable, fecha_inicio, fecha_fin, orden_id, orden_fecha)
        empleados = []
        if role == "jefe":
            empleados = UsuarioRepository.get_by_role("empleado")
        return pedidos, empleados

    @staticmethod
    def get_create_data():
        clientes = ClienteRepository.get_all()
        empleados = UsuarioRepository.get_by_role("empleado")
        return clientes, empleados

    @staticmethod
    def create_pedido(tipo_cliente, cliente_existente, nombre, telefono, correo, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        if tipo_cliente == "existente":
            cliente_id = cliente_existente
        else:
            cliente_id = ClienteRepository.create(nombre, telefono, correo)

        return PedidoRepository.create(cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)

    @staticmethod
    def actualizar_estado(pedido_id, nuevo_estado, rol, user_id):
        pedido = PedidoRepository.get_by_id(pedido_id)
        if not pedido:
            return False, "Pedido no encontrado", 404
        
        if pedido["estado"] == "terminado":
            return False, "El pedido ya está terminado", 400
            
        if rol == "empleado" and pedido["responsable_id"] != user_id:
            return False, "Acceso denegado", 403
            
        PedidoRepository.update_estado(pedido_id, nuevo_estado)
        return True, "Estado actualizado", 200

    @staticmethod
    def get_detail(pedido_id, rol, user_id):
        from app.infrastructure.repositories.produccion_repository import ProduccionRepository
        
        pedido = PedidoRepository.get_detail_by_id(pedido_id)
        if not pedido:
            return False, None, None, 404
            
        if rol == "empleado" and pedido["responsable_id"] != user_id:
            return False, None, None, 403
            
        produccion = ProduccionRepository.get_by_pedido(pedido_id)
        return True, pedido, produccion, 200

    @staticmethod
    def get_edit_data(pedido_id):
        pedido = PedidoRepository.get_by_id(pedido_id)
        if not pedido:
            return False, None, None, None, 404
            
        if pedido["estado"] == "terminado":
            return False, None, None, None, 400
            
        clientes = ClienteRepository.get_all()
        empleados = UsuarioRepository.get_by_role("empleado")
        
        return True, pedido, clientes, empleados, 200

    @staticmethod
    def update_pedido(pedido_id, cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        PedidoRepository.update(pedido_id, cliente_id, descripcion, fecha_entrega, valor_total, anticipo, responsable_id)
        return True

    @staticmethod
    def delete_pedido(pedido_id):
        PedidoRepository.delete(pedido_id)
        return True
