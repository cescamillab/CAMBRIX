from app.infrastructure.repositories.usuario_repository import UsuarioRepository

class EmpleadoService:
    @staticmethod
    def get_all_empleados():
        return UsuarioRepository.get_all()

    @staticmethod
    def get_empleados_only():
        return UsuarioRepository.get_by_role("empleado")

    @staticmethod
    def create_empleado(nombre, username, password, rol):
        if not nombre or not username or not password or not rol:
            return False, "Todos los campos son obligatorios"
        try:
            UsuarioRepository.create(nombre, username, password, rol)
            return True, "Empleado creado exitosamente"
        except Exception as e:
            return False, f"Error al crear empleado: {e}"

    @staticmethod
    def update_empleado(id, nombre, username, rol, password=None):
        if not nombre or not username or not rol:
            return False, "Nombre, usuario y rol son obligatorios"
        try:
            UsuarioRepository.update(id, nombre, username, rol, password)
            return True, "Empleado actualizado exitosamente"
        except Exception as e:
            return False, f"Error al actualizar empleado: {e}"

    @staticmethod
    def delete_empleado(id, current_user_id):
        if id == current_user_id:
            return False, "No puedes eliminar tu propia cuenta"
        try:
            UsuarioRepository.delete(id)
            return True, "Empleado eliminado exitosamente"
        except Exception as e:
            return False, f"Error al eliminar empleado: {e}"
