from app.models.pedido_model import PedidoModel
from app.models.material_model import MaterialModel
from app.models.produccion_model import ProduccionModel

class DashboardService:
    @staticmethod
    def get_metrics(rol, user_id=None):
        materiales_bajos = MaterialModel.get_low_stock()

        if rol == "jefe":
            total = PedidoModel.count_total()
            pendientes = PedidoModel.count_by_status("pendiente")
            en_proceso = PedidoModel.count_by_status("en_proceso")
            terminados = PedidoModel.count_by_status("terminado")
            total_facturado = PedidoModel.sum_total_invoiced()
            total_pendiente = PedidoModel.sum_total_pending_balance()
            estados = PedidoModel.group_by_status()
            ingresos = PedidoModel.get_monthly_income()

            top_materiales = ProduccionModel.get_top_materiales()
            top_clientes = PedidoModel.get_top_clientes()
            ultimos_pedidos = PedidoModel.get_latest()
        else:
            total = PedidoModel.count_total_for_user(user_id)
            pendientes = PedidoModel.count_by_status_for_user(user_id, "pendiente")
            en_proceso = PedidoModel.count_by_status_for_user(user_id, "en_proceso")
            terminados = PedidoModel.count_by_status_for_user(user_id, "terminado")
            total_facturado = PedidoModel.sum_total_invoiced_for_user(user_id)
            total_pendiente = PedidoModel.sum_total_pending_balance_for_user(user_id)
            estados = PedidoModel.group_by_status_for_user(user_id)
            ingresos = PedidoModel.get_monthly_income_for_user(user_id)

            top_materiales = []
            top_clientes = []
            ultimos_pedidos = PedidoModel.get_latest_for_user(user_id)

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
