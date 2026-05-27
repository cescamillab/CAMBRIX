"""
app/application/services/empleado_service.py - Servicio de Gestión de Empleados
==================================================================================
Responsabilidad: Contiene toda la lógica de negocio para la administración del
personal (usuarios del sistema). Aplica validaciones antes de delegar las
operaciones de base de datos al `UsuarioRepository`.

Acceso restringido:
    Todas las operaciones de este servicio (crear, editar, eliminar empleados)
    están reservadas únicamente para el rol "jefe". Esta restricción se aplica
    en el Blueprint `empleados/routes.py` con la función helper `es_jefe()`.
    El servicio asume que quien lo llama ya tiene los permisos necesarios.

Validaciones implementadas:
    - create_empleado: Verifica que todos los campos sean obligatorios.
    - update_empleado: Verifica que nombre, username y rol no estén vacíos.
    - delete_empleado: Previene que un jefe se elimine a sí mismo.

Patrón de retorno (bool, str):
    Los métodos que pueden fallar retornan una tupla `(éxito, mensaje)`:
    - (True, "Mensaje de éxito")
    - (False, "Mensaje de error descriptivo")
    Esto permite al Blueprint mostrar el mensaje apropiado con `flash()`.
"""
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class EmpleadoService:
    """
    Servicio de gestión de empleados/usuarios del sistema.
    """

    @staticmethod
    def get_all_empleados():
        """
        Obtiene la lista completa de todos los usuarios registrados en el sistema.

        Incluye tanto a los jefes como a los empleados. Usado para poblar la
        tabla de gestión de personal en la vista `listar_empleados.html`.

        Returns:
            list[dict]: Lista de todos los usuarios con campos: id, nombre, username, rol.
        """
        return UsuarioRepository.get_all()

    @staticmethod
    def get_empleados_only():
        """
        Obtiene únicamente los usuarios con rol "empleado".

        Usado en contextos donde solo se necesita listar el personal operativo,
        no los jefes (ej. selectores de responsable en formularios de pedido).

        Returns:
            list[dict]: Lista de usuarios con rol "empleado".
        """
        return UsuarioRepository.get_by_role("empleado")

    @staticmethod
    def create_empleado(nombre, username, password, rol):
        """
        Crea un nuevo empleado/usuario en el sistema, con validación previa.

        Validaciones:
            - Todos los campos son obligatorios (nombre, username, password, rol).
            - Si alguno está vacío o es None, retorna error sin llamar a la DB.

        Args:
            nombre   (str): Nombre completo del empleado.
            username (str): Nombre de usuario único para el login.
            password (str): Contraseña (texto plano actualmente).
            rol      (str): Rol asignado: "jefe" o "empleado".

        Returns:
            tuple(bool, str):
                - (True, "Empleado creado exitosamente") si se creó correctamente.
                - (False, "Todos los campos son obligatorios") si falta algún campo.
                - (False, "Error al crear empleado: <detalle>") si hay error en DB
                  (ej. username duplicado).
        """
        # Validar que ningún campo esté vacío o sea None
        if not nombre or not username or not password or not rol:
            return False, "Todos los campos son obligatorios"
        try:
            UsuarioRepository.create(nombre, username, password, rol)
            return True, "Empleado creado exitosamente"
        except Exception as e:
            # Capturar errores de DB (ej. IntegrityError por username duplicado)
            return False, f"Error al crear empleado: {e}"

    @staticmethod
    def update_empleado(id, nombre, username, rol, password=None):
        """
        Actualiza los datos de un empleado existente.

        La contraseña es opcional: si se proporciona una nueva, se actualiza.
        Si no (password=None o password=""), se conserva la contraseña actual.

        Validaciones:
            - nombre, username y rol son campos obligatorios para la actualización.

        Args:
            id       (int):      ID del usuario a actualizar.
            nombre   (str):      Nuevo nombre completo.
            username (str):      Nuevo nombre de usuario.
            rol      (str):      Nuevo rol ("jefe" o "empleado").
            password (str|None): Nueva contraseña. Si es None/vacío, no se cambia.

        Returns:
            tuple(bool, str):
                - (True, "Empleado actualizado exitosamente") si fue exitoso.
                - (False, "Nombre, usuario y rol son obligatorios") si falta campo requerido.
                - (False, "Error al actualizar empleado: <detalle>") si hay error en DB.
        """
        # Validar campos obligatorios (password es opcional en actualización)
        if not nombre or not username or not rol:
            return False, "Nombre, usuario y rol son obligatorios"
        try:
            UsuarioRepository.update(id, nombre, username, rol, password)
            return True, "Empleado actualizado exitosamente"
        except Exception as e:
            return False, f"Error al actualizar empleado: {e}"

    @staticmethod
    def delete_empleado(id, current_user_id):
        """
        Elimina un empleado del sistema, con protección contra auto-eliminación.

        Regla de negocio crítica: Un usuario NO puede eliminarse a sí mismo.
        Esto previene que el único jefe del sistema quede sin acceso administrativo
        al eliminar su propia cuenta por error.

        Args:
            id              (int): ID del empleado a eliminar.
            current_user_id (int): ID del usuario autenticado que está realizando
                                   la acción (obtenido de `session["user_id"]`).

        Returns:
            tuple(bool, str):
                - (True, "Empleado eliminado exitosamente") si se eliminó.
                - (False, "No puedes eliminar tu propia cuenta") si se intenta
                  el auto-borrado.
                - (False, "Error al eliminar empleado: <detalle>") si hay error en DB.
        """
        # Protección: impedir que el usuario activo se elimine a sí mismo
        if id == current_user_id:
            return False, "No puedes eliminar tu propia cuenta"
        try:
            UsuarioRepository.delete(id)
            return True, "Empleado eliminado exitosamente"
        except Exception as e:
            return False, f"Error al eliminar empleado: {e}"
