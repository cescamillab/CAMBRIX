"""
app/application/services/dashboard_service.py - Servicio del Dashboard
========================================================================
Responsabilidad: Recopila y combina todos los datos necesarios para renderizar
el panel de control (Dashboard) de CAMBRIX. Este servicio actúa como un
"aggregator": llama a múltiples repositorios y consolida sus resultados en
un único diccionario de métricas listo para ser pasado a la plantilla HTML.

Lógica de doble vista (Jefe vs Empleado):
    El Dashboard muestra información diferente según el rol del usuario:

    Vista JEFE ("jefe"):
        - KPIs globales: total de pedidos, facturación total, saldo pendiente.
        - Gráficas: distribución por estado, ingresos mensuales globales.
        - Widgets adicionales: Top 5 materiales más usados, Top 5 clientes,
          últimos 5 pedidos de toda la empresa.

    Vista EMPLEADO ("empleado"):
        - KPIs personales: solo sus propios pedidos y sus valores.
        - Gráficas: distribución de SUS pedidos, sus ingresos mensuales.
        - Widgets adicionales: No muestra top materiales ni top clientes
          (información estratégica reservada al jefe).
          Solo muestra sus últimos 5 pedidos.

    En ambos casos se muestra la alerta de materiales con stock bajo, ya que
    es información operativa relevante para cualquier usuario.
"""
from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.repositories.produccion_repository import ProduccionRepository


class DashboardService:
    """
    Servicio de datos para el panel de control principal.
    """

    @staticmethod
    def get_metrics(rol, user_id=None):
        """
        Recopila todas las métricas del dashboard según el rol del usuario.

        Determina qué conjunto de consultas ejecutar basándose en el rol,
        y retorna un diccionario unificado que la plantilla `dashboard.html`
        puede consumir con variables de mismo nombre en ambos casos.

        Args:
            rol     (str):      Rol del usuario autenticado: "jefe" o "empleado".
            user_id (int|None): ID del usuario autenticado. Requerido si rol == "empleado"
                                para filtrar los pedidos por responsable.

        Returns:
            dict: Diccionario con todas las métricas necesarias para el dashboard.
                  Claves disponibles:
                    - total         (int):   Total de pedidos.
                    - pendientes    (int):   Pedidos en estado "pendiente".
                    - en_proceso    (int):   Pedidos en estado "en_proceso".
                    - terminados    (int):   Pedidos en estado "terminado".
                    - total_facturado (float): Suma del valor_total de todos los pedidos.
                    - total_pendiente (float): Suma del saldo (valor_total - anticipo).
                    - estados       (list):  Datos para gráfico de torta por estado.
                    - ingresos      (list):  Datos para gráfico de barras mensual.
                    - materiales_bajos (list): Materiales con stock crítico (alerta).
                    - top_materiales(list):  Top 5 materiales usados (solo jefe).
                    - top_clientes  (list):  Top 5 clientes por facturación (solo jefe).
                    - ultimos_pedidos(list): Últimos 5 pedidos relevantes para el usuario.
        """
        # Esta alerta de stock se muestra para TODOS los roles
        materiales_bajos = MaterialRepository.get_low_stock()

        if rol == "jefe":
            # ---------------------------------------------------------------
            # Vista del JEFE: datos globales de toda la empresa
            # ---------------------------------------------------------------
            total = PedidoRepository.count_total()
            pendientes = PedidoRepository.count_by_status("pendiente")
            en_proceso = PedidoRepository.count_by_status("en_proceso")
            terminados = PedidoRepository.count_by_status("terminado")
            total_facturado = PedidoRepository.sum_total_invoiced()
            total_pendiente = PedidoRepository.sum_total_pending_balance()
            estados = PedidoRepository.group_by_status()
            ingresos = PedidoRepository.get_monthly_income()

            # Widgets analíticos exclusivos del jefe
            top_materiales = ProduccionRepository.get_top_materiales()
            top_clientes = PedidoRepository.get_top_clientes()
            ultimos_pedidos = PedidoRepository.get_latest()
        else:
            # ---------------------------------------------------------------
            # Vista del EMPLEADO: datos filtrados por su responsable_id
            # ---------------------------------------------------------------
            total = PedidoRepository.count_total_for_user(user_id)
            pendientes = PedidoRepository.count_by_status_for_user(user_id, "pendiente")
            en_proceso = PedidoRepository.count_by_status_for_user(user_id, "en_proceso")
            terminados = PedidoRepository.count_by_status_for_user(user_id, "terminado")
            total_facturado = PedidoRepository.sum_total_invoiced_for_user(user_id)
            total_pendiente = PedidoRepository.sum_total_pending_balance_for_user(user_id)
            estados = PedidoRepository.group_by_status_for_user(user_id)
            ingresos = PedidoRepository.get_monthly_income_for_user(user_id)

            # El empleado no tiene acceso a información estratégica de la empresa
            top_materiales = []
            top_clientes = []
            ultimos_pedidos = PedidoRepository.get_latest_for_user(user_id)

        # Retornar todas las métricas en un dict único para la plantilla
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
