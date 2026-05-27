"""
app/presentation/blueprints/dashboard/routes.py - Controlador del Dashboard
=============================================================================
Responsabilidad: Gestiona la ruta del panel de control principal de CAMBRIX.
Es la primera página que ve el usuario tras iniciar sesión.

Blueprint registrado como: "dashboard"
Prefijo de URL: /dashboard

Rutas expuestas:
    GET /dashboard/ → Renderiza el panel principal con métricas y gráficas.

Protección de acceso:
    La ruta está protegida con `@login_required`. Solo usuarios con sesión
    activa pueden acceder. Los no autenticados son redirigidos a `/` (login).

Vista adaptativa según rol:
    El dashboard muestra información diferente dependiendo del rol en sesión:
    - "jefe":     KPIs globales, top clientes, top materiales, todos los pedidos.
    - "empleado": KPIs personales (solo sus pedidos), sin información estratégica.
    La lógica de qué datos obtener está encapsulada en `DashboardService.get_metrics()`.

Plantilla utilizada:
    - dashboard.html: Recibe todas las métricas como variables de contexto
      y las renderiza en tarjetas KPI, gráficos Chart.js y tablas resumen.
"""
from flask import Blueprint, render_template, session
from app.core.security import login_required
from app.application.services.dashboard_service import DashboardService

# Definición del Blueprint con prefijo de URL /dashboard
dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
    template_folder="templates"
)


@dashboard_bp.route("/")
@login_required  # Protege la ruta: redirige a login si no hay sesión activa
def home():
    """
    Vista principal del panel de control (Dashboard).

    Lee el rol y el ID del usuario desde la sesión activa y se los pasa
    al `DashboardService` para obtener el conjunto correcto de métricas.
    Luego pasa todas las métricas como variables de contexto a la plantilla.

    Variables de sesión utilizadas:
        - session["rol"]:     Para determinar qué vista mostrar (jefe vs empleado).
        - session["user_id"]: Para filtrar datos por responsable si es empleado.

    Variables pasadas a la plantilla `dashboard.html`:
        - total            (int):   Total de pedidos relevantes para el usuario.
        - pendientes       (int):   Pedidos en estado "pendiente".
        - en_proceso       (int):   Pedidos en estado "en_proceso".
        - terminados       (int):   Pedidos en estado "terminado".
        - total_facturado  (float): Suma del valor total de los pedidos.
        - total_pendiente  (float): Suma del saldo por cobrar.
        - rol              (str):   Rol del usuario (para condicionar la vista en el HTML).
        - estados          (list):  Datos para el gráfico de torta (distribución por estado).
        - ingresos         (list):  Datos para el gráfico de barras (ingresos mensuales).
        - materiales_bajos (list):  Materiales con stock crítico (alerta de reabastecimiento).
        - top_materiales   (list):  Top 5 materiales más usados (solo jefe, vacío para empleado).
        - top_clientes     (list):  Top 5 clientes por facturación (solo jefe, vacío para empleado).
        - ultimos_pedidos  (list):  Últimos 5 pedidos del usuario.

    Returns:
        Response: Renderizado de `dashboard.html` con todas las métricas.
    """
    rol = session.get("rol")
    user_id = session.get("user_id")

    # Obtener todas las métricas del servicio (el servicio decide qué consultar según el rol)
    metrics = DashboardService.get_metrics(rol, user_id)

    # Desempaquetar el diccionario de métricas como variables individuales para la plantilla
    return render_template(
        "dashboard.html",
        total=metrics["total"],
        pendientes=metrics["pendientes"],
        en_proceso=metrics["en_proceso"],
        terminados=metrics["terminados"],
        total_facturado=metrics["total_facturado"],
        total_pendiente=metrics["total_pendiente"],
        rol=rol,
        estados=metrics["estados"],
        ingresos=metrics["ingresos"],
        materiales_bajos=metrics["materiales_bajos"],
        top_materiales=metrics["top_materiales"],
        top_clientes=metrics["top_clientes"],
        ultimos_pedidos=metrics["ultimos_pedidos"]
    )
