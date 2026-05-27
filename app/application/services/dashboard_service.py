from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.produccion_repository import ProduccionRepository

class DashboardService:
    @staticmethod
    def get_metrics(rol, user_id=None):
        materiales_bajos = MaterialRepository.get_low_stock()

        if rol == "jefe":
            total = PedidoRepository.count_total()
            pendientes = PedidoRepository.count_by_status("pendiente")
            en_proceso = PedidoRepository.count_by_status("en_proceso")
            terminados = PedidoRepository.count_by_status("terminado")
            total_facturado = PedidoRepository.sum_total_invoiced()
            total_pendiente = PedidoRepository.sum_total_pending_balance()
            estados = PedidoRepository.group_by_status()
            ingresos = PedidoRepository.get_monthly_income()

            top_materiales = ProduccionRepository.get_top_materiales()
            top_clientes = PedidoRepository.get_top_clientes()
            ultimos_pedidos = PedidoRepository.get_latest()
        else:
            total = PedidoRepository.count_total_for_user(user_id)
            pendientes = PedidoRepository.count_by_status_for_user(user_id, "pendiente")
            en_proceso = PedidoRepository.count_by_status_for_user(user_id, "en_proceso")
            terminados = PedidoRepository.count_by_status_for_user(user_id, "terminado")
            total_facturado = PedidoRepository.sum_total_invoiced_for_user(user_id)
            total_pendiente = PedidoRepository.sum_total_pending_balance_for_user(user_id)
            estados = PedidoRepository.group_by_status_for_user(user_id)
            ingresos = PedidoRepository.get_monthly_income_for_user(user_id)

            top_materiales = []
            top_clientes = []
            ultimos_pedidos = PedidoRepository.get_latest_for_user(user_id)

        return {
            "total": total,
            "pendientes": pendientes,
            "en_proceso": en_proceso,
            "terminados": terminados,
            "total_facturado": total_facturado,
            "total_pendiente": total_pendiente,
            "estados": estados,
            "ingresos": ingresos,
            "materiales_bajos": materiales_bajos,
            "top_materiales": top_materiales,
            "top_clientes": top_clientes,
            "ultimos_pedidos": ultimos_pedidos
        }
