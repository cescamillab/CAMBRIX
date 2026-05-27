"""
app/presentation/blueprints/inventarios/routes.py - Controlador de Inventarios
================================================================================
Responsabilidad: Gestiona todas las rutas HTTP del módulo de control de
inventario: listado, creación, edición, eliminación de materiales, registro
de movimientos e historial.

Blueprint registrado como: "inventarios"
Prefijo de URL: /inventarios

Rutas expuestas:
    GET      /inventarios/                          → Lista materiales (con filtros).
    GET/POST /inventarios/crear                     → Formulario para nuevo material.
    GET/POST /inventarios/editar/<id>               → Formulario para editar material.
    POST     /inventarios/eliminar/<id>             → Elimina un material.
    GET/POST /inventarios/movimiento/<material_id>  → Registra entrada/salida de stock.
    GET      /inventarios/historial/<material_id>   → Historial de movimientos del material.

Control de Acceso por Ruta:
    - Todas las rutas: `@login_required` (autenticación básica).
    - Crear, Editar, Eliminar: Solo "jefe" (verificado dentro de la vista).
    - Movimiento e Historial: Cualquier usuario autenticado.

Filtros Disponibles en la Lista:
    La vista de lista soporta dos filtros por query string (GET):
    - `?stock_status=critico`: Solo materiales con stock bajo.
    - `?stock_status=normal`:  Solo materiales con stock suficiente.
    - `?categoria=Madera`:     Solo materiales de esa categoría.
    Los filtros se combinan y se mantienen al recargar la página.

Plantillas utilizadas:
    - lista_materiales.html:      Tabla de materiales con filtros y acciones.
    - crear_material.html:        Formulario de creación.
    - editar_material.html:       Formulario de edición pre-poblado.
    - registrar_movimiento.html:  Formulario de entrada/salida de stock.
    - historial_material.html:    Tabla del historial de movimientos.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.core.security import login_required
from app.application.services.inventario_service import InventarioService

# Definición del Blueprint con prefijo /inventarios
inventarios_bp = Blueprint(
    "inventarios",
    __name__,
    url_prefix="/inventarios",
    template_folder="templates"
)


# ===========================================================================
# LISTAR MATERIALES (con filtros opcionales)
# ===========================================================================
@inventarios_bp.route("/")
@login_required
def listar_materiales():
    """
    Muestra la lista de todos los materiales del inventario con filtros opcionales.

    Lee los filtros de la URL (query string) y los pasa al servicio para obtener
    los materiales filtrados. También obtiene el conteo de alertas de stock bajo
    y las categorías disponibles para los controles de filtro en el HTML.

    Query Parameters:
        stock_status (str): Filtro de stock. Valores: "critico", "normal" o vacío (todos).
        categoria    (str): Nombre de categoría para filtrar. Vacío = todas.

    Variables enviadas a la plantilla:
        - materiales           (list): Materiales según los filtros aplicados.
        - alerta_stock         (dict): {"bajos": int} con el conteo de alertas.
        - categorias           (list): Lista de strings con categorías únicas.
        - stock_status         (str):  El filtro activo (para resaltar en la UI).
        - categoria_seleccionada(str): La categoría activa (para el selector).

    Returns:
        Response: Renderizado de `lista_materiales.html`.
    """
    # Obtener filtros de la URL, con string vacío como valor por defecto
    stock_status = request.args.get('stock_status', '')
    categoria = request.args.get('categoria', '')

    # El servicio retorna los tres datos necesarios para la vista en una sola llamada
    materiales, alerta_stock, categorias = InventarioService.get_material_list(
        stock_status, categoria
    )
    return render_template(
        "lista_materiales.html",
        materiales=materiales,
        alerta_stock=alerta_stock,
        categorias=categorias,
        stock_status=stock_status,
        categoria_seleccionada=categoria
    )


# ===========================================================================
# CREAR MATERIAL (Solo Jefe)
# ===========================================================================
@inventarios_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear_material():
    """
    Muestra y procesa el formulario para crear un nuevo material en el inventario.

    Acceso: Exclusivo para el rol "jefe". Si un empleado intenta acceder,
    recibe una respuesta de texto "Acceso no autorizado" (sin redirección).
    Esto es un comportamiento simple; podría mejorarse con `abort(403)`.

    GET /inventarios/crear:
        Renderiza el formulario vacío de creación.

    POST /inventarios/crear:
        Recibe los datos del formulario, crea el material y redirige a la lista.

    Campos del formulario esperados:
        - nombre:       Nombre del material.
        - categoria:    Categoría de agrupación.
        - unidad:       Unidad de medida (ej. "ml", "kg").
        - stock:        Stock inicial.
        - stock_minimo: Umbral mínimo para alertas.
        - costo:        Costo unitario de compra.

    Returns:
        Response: Formulario de creación (GET) o redirección a lista (POST).
    """
    if session.get("rol") != "jefe":
        return "Acceso no autorizado"

    if request.method == "POST":
        # Extraer todos los campos del formulario
        nombre = request.form["nombre"]
        categoria = request.form["categoria"]
        unidad = request.form["unidad"]
        stock = request.form["stock"]
        stock_minimo = request.form["stock_minimo"]
        costo = request.form["costo"]

        InventarioService.create_material(nombre, categoria, unidad, stock, stock_minimo, costo)
        return redirect(url_for("inventarios.listar_materiales"))

    # GET: mostrar formulario vacío
    return render_template("crear_material.html")


# ===========================================================================
# EDITAR MATERIAL (Solo Jefe)
# ===========================================================================
@inventarios_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_material(id):
    """
    Muestra y procesa el formulario de edición de un material existente.

    Acceso: Exclusivo para el rol "jefe".

    GET /inventarios/editar/<id>:
        Obtiene los datos actuales del material y los pre-popula en el formulario.

    POST /inventarios/editar/<id>:
        Actualiza los datos del material (excepto stock_actual) y redirige a la lista.

    NOTA: El `stock_actual` no es editable desde este formulario. Solo puede
    cambiar mediante el registro de un movimiento de inventario, para mantener
    la trazabilidad en `movimientos_inventario`.

    Args:
        id (int): ID del material a editar (capturado de la URL).

    Campos del formulario esperados (POST):
        - nombre, categoria, unidad, stock_minimo, costo.
        (El stock_actual se omite intencionalmente)

    Returns:
        Response: Formulario de edición (GET) o redirección a lista (POST).
    """
    if session.get("rol") != "jefe":
        return "Acceso no autorizado"

    # Obtener datos actuales del material para pre-poblar el formulario en GET
    material = InventarioService.get_material(id)

    if request.method == "POST":
        nombre = request.form["nombre"]
        categoria = request.form["categoria"]
        unidad = request.form["unidad"]
        stock_minimo = request.form["stock_minimo"]
        costo = request.form["costo"]

        InventarioService.update_material(id, nombre, categoria, unidad, stock_minimo, costo)
        return redirect(url_for("inventarios.listar_materiales"))

    # GET: mostrar formulario pre-poblado con los datos actuales del material
    return render_template("editar_material.html", material=material)


# ===========================================================================
# ELIMINAR MATERIAL (Solo Jefe)
# ===========================================================================
@inventarios_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_material(id):
    """
    Elimina un material y todos sus registros relacionados.

    Solo acepta POST para evitar eliminaciones accidentales por GET.
    Muestra un mensaje flash indicando si la operación fue exitosa o falló.

    La eliminación es en cascada (manejada por el repositorio):
    1. Elimina registros en `produccion_materiales`.
    2. Elimina registros en `movimientos_inventario`.
    3. Elimina el material de `materiales`.
    Si algún paso falla, se hace rollback y se muestra el error.

    Args:
        id (int): ID del material a eliminar.

    Returns:
        Response: Redirección a `inventarios.listar_materiales` con mensaje flash.
    """
    if session.get("rol") != "jefe":
        return "Acceso no autorizado"

    success, msg = InventarioService.delete_material(id)
    flash(msg, "success" if success else "danger")

    return redirect(url_for("inventarios.listar_materiales"))


# ===========================================================================
# REGISTRAR MOVIMIENTO DE INVENTARIO
# ===========================================================================
@inventarios_bp.route("/movimiento/<int:material_id>", methods=["GET", "POST"])
@login_required
def registrar_movimiento(material_id):
    """
    Gestiona el registro manual de entradas y salidas de stock de un material.

    Accesible para cualquier usuario autenticado (jefe y empleados).

    GET /inventarios/movimiento/<material_id>:
        Muestra el formulario de movimiento con los datos actuales del material.

    POST /inventarios/movimiento/<material_id>:
        Procesa el movimiento. Si falla la validación (stock insuficiente,
        material no encontrado), retorna el mensaje de error directamente como texto.
        Si tiene éxito, redirige a la lista de materiales.

    NOTA: El manejo de error en POST (`return msg`) es simple y podría mejorarse
    usando flash messages y redirección en lugar de retornar texto plano.

    Args:
        material_id (int): ID del material sobre el que se registra el movimiento.

    Campos del formulario esperados (POST):
        - tipo     (str):   "entrada" o "salida".
        - cantidad (float): Cantidad de unidades del movimiento.
        - motivo   (str):   Descripción del motivo del movimiento.

    Returns:
        Response: Formulario (GET), redirección a lista (POST exitoso),
                  o texto de error (POST fallido).
    """
    # Obtener datos del material para mostrar en el formulario (nombre, stock actual, etc.)
    material = InventarioService.get_material(material_id)

    if request.method == "POST":
        tipo = request.form["tipo"]
        cantidad = float(request.form["cantidad"])  # Convertir a float desde string del form
        motivo = request.form["motivo"]

        success, msg = InventarioService.registrar_movimiento(material_id, tipo, cantidad, motivo)
        if not success:
            # Retornar el mensaje de error directamente (simplificado)
            return msg

        return redirect(url_for("inventarios.listar_materiales"))

    # GET: mostrar formulario de movimiento con datos del material
    return render_template("registrar_movimiento.html", material=material)


# ===========================================================================
# HISTORIAL DE MOVIMIENTOS DE UN MATERIAL
# ===========================================================================
@inventarios_bp.route("/historial/<int:material_id>")
@login_required
def historial_material(material_id):
    """
    Muestra el historial completo de movimientos de un material específico.

    Muestra todos los movimientos (entradas y salidas) en orden cronológico
    inverso, incluyendo referencia al pedido relacionado si el movimiento
    provino de producción.

    Accesible para cualquier usuario autenticado.

    Args:
        material_id (int): ID del material cuyo historial se quiere consultar.

    Variables enviadas a la plantilla:
        - material    (dict): Datos del material (nombre, stock actual, etc.).
        - movimientos (list): Lista de movimientos ordenados por fecha DESC.

    Returns:
        Response: Renderizado de `historial_material.html`.
    """
    material, movimientos = InventarioService.get_historial(material_id)

    return render_template(
        "historial_material.html",
        material=material,
        movimientos=movimientos
    )
