"""
app/application/services/pedido_service.py - Servicio de Gestión de Pedidos
=============================================================================
Responsabilidad: Contiene toda la lógica de negocio relacionada con los
pedidos. Es el servicio más complejo del sistema por la cantidad de reglas
de negocio y la necesidad de coordinar múltiples repositorios.

Reglas de Negocio Implementadas:
    1. Solo el "jefe" puede crear, editar y eliminar pedidos.
       (Aplicado en el Blueprint con `@role_required("jefe")`)
    2. Un pedido "terminado" NO puede cambiar de estado.
    3. Un "empleado" solo puede ver y cambiar el estado de SUS pedidos
       (donde él es el responsable_id).
    4. Un empleado NO puede editar los datos de un pedido, solo su estado.
    5. Al crear un pedido, se puede crear el cliente "al vuelo" (nuevo cliente)
       o reutilizar uno existente.

Gestión de Clientes al Crear un Pedido:
    El formulario de creación de pedidos tiene un campo `tipo_cliente`:
    - "existente": El jefe selecciona un cliente ya registrado de un dropdown.
                   Se usa su ID directamente.
    - "nuevo":     El jefe ingresa los datos de un nuevo cliente (nombre, teléfono, correo).
                   `ClienteRepository.create()` lo registra y retorna el nuevo ID,
                   que se usa inmediatamente para el pedido.

Patrón de retorno multi-valor:
    Los métodos que pueden fallar con distintos códigos HTTP retornan
    tuplas que incluyen el código de estado:
    (success: bool, data..., status_code: int)
    El Blueprint usa el status_code para llamar a `abort(status_code)` si es necesario.
"""
from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.cliente_repository import ClienteRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class PedidoService:
    """
    Servicio de lógica de negocio para la gestión de pedidos.
    """

    @staticmethod
    def get_filtered(role, user_id, busqueda, estado, responsable,
                     fecha_inicio=None, fecha_fin=None, orden_id=None, orden_fecha=None):
        """
        Obtiene la lista de pedidos filtrada según el rol del usuario y los filtros aplicados.

        Para el jefe, también obtiene la lista de empleados para el filtro de responsable.
        Para el empleado, la lista de empleados es vacía (no tiene ese filtro disponible).

        Args:
            role        (str):       Rol del usuario ("jefe" o "empleado").
            user_id     (int):       ID del usuario autenticado.
            busqueda    (str):       Término de búsqueda por nombre de cliente.
            estado      (str):       Filtro de estado del pedido.
            responsable (str):       Filtro por responsable (ID como string, o vacío).
            fecha_inicio(str|None):  Fecha inicio del rango de entrega.
            fecha_fin   (str|None):  Fecha fin del rango de entrega.
            orden_id    (str|None):  Ordenamiento por ID ("asc"/"desc").
            orden_fecha (str|None):  Ordenamiento por fecha ("asc"/"desc").

        Returns:
            tuple(list, list):
                - pedidos   (list[dict]): Pedidos filtrados con datos enriquecidos.
                - empleados (list[dict]): Lista de empleados para el filtro (solo para jefe).
        """
        pedidos = PedidoRepository.filter_pedidos(
            role, user_id, busqueda, estado, responsable,
            fecha_inicio, fecha_fin, orden_id, orden_fecha
        )
        empleados = []
        # Solo el jefe necesita la lista de empleados para filtrar por responsable
        if role == "jefe":
            empleados = UsuarioRepository.get_by_role("empleado")
        return pedidos, empleados

    @staticmethod
    def get_create_data():
        """
        Obtiene los datos necesarios para renderizar el formulario de creación de pedidos.

        Retorna los clientes existentes (para el selector de cliente) y los
        empleados (para el selector de responsable).

        Returns:
            tuple(list, list):
                - clientes  (list[dict]): Todos los clientes registrados.
                - empleados (list[dict]): Todos los usuarios con rol "empleado".
        """
        clientes = ClienteRepository.get_all()
        empleados = UsuarioRepository.get_by_role("empleado")
        return clientes, empleados

    @staticmethod
    def create_pedido(tipo_cliente, cliente_existente, nombre, telefono, correo,
                      descripcion, fecha_entrega, valor_total, anticipo, responsable_id):
        """
        Crea un nuevo pedido, gestionando la creación del cliente si es necesario.

        Lógica de tipo_cliente:
            - "existente": Usa el `cliente_existente` (ID) directamente.
            - Cualquier otro valor (ej. "nuevo"): Crea el cliente con nombre,
              teléfono y correo, y obtiene el ID generado.

        Args:
            tipo_cliente      (str):   "existente" o "nuevo".
            cliente_existente (str):   ID del cliente existente (solo si tipo="existente").
            nombre            (str):   Nombre del nuevo cliente (solo si tipo="nuevo").
            telefono          (str):   Teléfono del nuevo cliente.
            correo            (str):   Correo del nuevo cliente.
            descripcion       (str):   Descripción del trabajo a realizar.
            fecha_entrega     (str):   Fecha límite de entrega 'YYYY-MM-DD'.
            valor_total       (str):   Precio total acordado (viene como string del form).
            anticipo          (str):   Monto adelantado (viene como string del form).
            responsable_id    (str):   ID del empleado responsable (string del form).

        Returns:
            int: ID del nuevo pedido creado en la base de datos.
        """
        if tipo_cliente == "existente":
            # Usar el ID del cliente seleccionado del dropdown
            cliente_id = cliente_existente
        else:
            # Registrar el nuevo cliente y obtener su ID auto-generado
            cliente_id = ClienteRepository.create(nombre, telefono, correo)

        return PedidoRepository.create(
            cliente_id, descripcion, fecha_entrega,
            valor_total, anticipo, responsable_id
        )

    @staticmethod
    def actualizar_estado(pedido_id, nuevo_estado, rol, user_id):
        """
        Cambia el estado de un pedido con validaciones de negocio.

        Validaciones aplicadas (en orden):
        1. El pedido debe existir.
        2. Un pedido "terminado" NO puede volver a cambiar de estado.
        3. Un empleado solo puede cambiar el estado de SUS propios pedidos.

        Args:
            pedido_id   (int): ID del pedido a actualizar.
            nuevo_estado(str): El nuevo estado deseado.
            rol         (str): Rol del usuario que realiza la acción.
            user_id     (int): ID del usuario que realiza la acción.

        Returns:
            tuple(bool, str, int): (éxito, mensaje, código_HTTP)
                - (True,  "Estado actualizado",    200) si fue exitoso.
                - (False, "Pedido no encontrado",   404) si no existe.
                - (False, "El pedido ya está terminado", 400) si ya está terminado.
                - (False, "Acceso denegado",         403) si el empleado no es el responsable.
        """
        # Validación 1: El pedido debe existir
        pedido = PedidoRepository.get_by_id(pedido_id)
        if not pedido:
            return False, "Pedido no encontrado", 404

        # Validación 2: Un pedido terminado es inmutable
        if pedido["estado"] == "terminado":
            return False, "El pedido ya está terminado", 400

        # Validación 3: El empleado solo puede modificar sus propios pedidos
        if rol == "empleado" and pedido["responsable_id"] != user_id:
            return False, "Acceso denegado", 403

        PedidoRepository.update_estado(pedido_id, nuevo_estado)
        return True, "Estado actualizado", 200

    @staticmethod
    def get_detail(pedido_id, rol, user_id):
        """
        Obtiene los datos completos de un pedido para la vista de detalle.

        Incluye los materiales usados en la producción del pedido.
        Aplica control de acceso: el empleado solo puede ver sus propios pedidos.

        Args:
            pedido_id (int): ID del pedido.
            rol       (str): Rol del usuario ("jefe" o "empleado").
            user_id   (int): ID del usuario.

        Returns:
            tuple(bool, dict|None, list|None, int):
                (éxito, pedido, produccion, código_HTTP)
                - (True,  pedido_dict, lista_produccion, 200) si fue exitoso.
                - (False, None, None, 404) si el pedido no existe.
                - (False, None, None, 403) si el empleado no tiene acceso.
        """
        # Importación local para evitar importaciones circulares en el módulo
        from app.infrastructure.repositories.produccion_repository import ProduccionRepository

        # Consultar datos completos con JOINs
        pedido = PedidoRepository.get_detail_by_id(pedido_id)
        if not pedido:
            return False, None, None, 404

        # Control de acceso: empleados solo ven sus pedidos
        if rol == "empleado" and pedido["responsable_id"] != user_id:
            return False, None, None, 403

        # Obtener materiales usados en la producción de este pedido
        produccion = ProduccionRepository.get_by_pedido(pedido_id)
        return True, pedido, produccion, 200

    @staticmethod
    def get_edit_data(pedido_id):
        """
        Obtiene todos los datos necesarios para el formulario de edición de un pedido.

        Aplica validaciones:
        1. El pedido debe existir.
        2. Un pedido "terminado" no puede editarse.

        Args:
            pedido_id (int): ID del pedido a editar.

        Returns:
            tuple(bool, dict|None, list|None, list|None, int):
                (éxito, pedido, clientes, empleados, código_HTTP)
                - (True,  pedido, clientes, empleados, 200) si fue exitoso.
                - (False, None, None, None, 404) si no existe.
                - (False, None, None, None, 400) si está terminado y no se puede editar.
        """
        pedido = PedidoRepository.get_by_id(pedido_id)
        if not pedido:
            return False, None, None, None, 404

        # Un pedido terminado no es editable (estado final)
        if pedido["estado"] == "terminado":
            return False, None, None, None, 400

        # Obtener datos para poblar los selectores del formulario
        clientes = ClienteRepository.get_all()
        empleados = UsuarioRepository.get_by_role("empleado")

        return True, pedido, clientes, empleados, 200

    @staticmethod
    def update_pedido(pedido_id, cliente_id, descripcion, fecha_entrega,
                      valor_total, anticipo, responsable_id):
        """
        Actualiza los datos de un pedido existente.

        Asume que las validaciones de acceso (jefe) y de estado (no terminado)
        ya fueron realizadas por `get_edit_data()` antes de llamar a este método.

        Args:
            pedido_id    (int):   ID del pedido.
            cliente_id   (str):   Nuevo ID del cliente.
            descripcion  (str):   Nueva descripción.
            fecha_entrega(str):   Nueva fecha límite.
            valor_total  (str):   Nuevo valor total.
            anticipo     (str):   Nuevo monto de anticipo.
            responsable_id(str):  Nuevo ID del responsable.

        Returns:
            bool: True siempre (las excepciones se propagan si ocurren).
        """
        PedidoRepository.update(
            pedido_id, cliente_id, descripcion, fecha_entrega,
            valor_total, anticipo, responsable_id
        )
        return True

    @staticmethod
    def delete_pedido(pedido_id):
        """
        Elimina un pedido permanentemente.

        PRECAUCIÓN: Esta acción no tiene reversa. El Blueprint aplica
        `@role_required("jefe")` antes de llegar aquí, garantizando que
        solo el jefe puede eliminar pedidos.

        Args:
            pedido_id (int): ID del pedido a eliminar.

        Returns:
            bool: True siempre.
        """
        PedidoRepository.delete(pedido_id)
        return True
