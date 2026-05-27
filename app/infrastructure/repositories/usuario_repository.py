"""
app/infrastructure/repositories/usuario_repository.py - Repositorio de Usuarios
=================================================================================
Responsabilidad: Encapsula TODAS las operaciones de base de datos sobre la
tabla `usuarios`. Ningún otro módulo del sistema escribe SQL directamente
sobre esta tabla.

Tabla gestionada: `usuarios`
    Columnas principales: id, nombre, username, password, rol

Roles del sistema:
    - "jefe":     Acceso total. Puede ver reportes, gestionar empleados,
                  crear/eliminar pedidos y materiales.
    - "empleado": Acceso restringido. Solo ve y trabaja sus propios pedidos.

NOTA DE SEGURIDAD IMPORTANTE:
    Las contraseñas se almacenan y comparan en TEXTO PLANO en la consulta
    de autenticación. Para producción, se recomienda migrar a hashing
    seguro usando `werkzeug.security` (generate_password_hash / check_password_hash)
    o la librería `bcrypt`.
"""
from app.infrastructure.database import get_connection


class UsuarioRepository:
    """
    Clase de repositorio estático para la tabla `usuarios`.

    Todos los métodos son `@staticmethod` porque no necesitan estado
    de instancia: cada método abre su propia conexión, ejecuta la
    consulta y cierra la conexión de forma independiente.
    """

    @staticmethod
    def authenticate(username, password):
        """
        Verifica las credenciales de un usuario contra la base de datos.

        Busca un registro en `usuarios` donde el `username` Y el `password`
        coincidan exactamente con los valores proporcionados.

        Args:
            username (str): El nombre de usuario ingresado en el formulario.
            password (str): La contraseña ingresada en el formulario (texto plano).

        Returns:
            dict | None: Un diccionario con todos los campos del usuario
                         (id, nombre, username, password, rol) si las
                         credenciales son correctas. Retorna `None` si no
                         se encuentra ningún usuario con esas credenciales.
        """
        connection = get_connection()
        # `dictionary=True` hace que fetchone() retorne un dict {columna: valor}
        # en lugar de una tupla posicional, lo que hace el código más legible.
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
        # Usar parámetros (%s) en lugar de concatenar strings PREVIENE la inyección SQL.
        cursor.execute(query, (username, password))
        user = cursor.fetchone()  # Retorna None si no hay coincidencia
        cursor.close()
        connection.close()
        return user

    @staticmethod
    def get_all():
        """
        Obtiene la lista completa de todos los usuarios registrados en el sistema.

        No retorna el campo `password` por seguridad (no es necesario para la
        gestión de usuarios en el frontend).

        Returns:
            list[dict]: Lista de diccionarios, uno por usuario, con los campos:
                        id, nombre, username, rol.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        # Se excluye explícitamente el campo `password` de la consulta
        cursor.execute("SELECT id, nombre, username, rol FROM usuarios")
        empleados = cursor.fetchall()
        cursor.close()
        connection.close()
        return empleados

    @staticmethod
    def get_by_role(role):
        """
        Obtiene todos los usuarios que tienen un rol específico.

        Usado principalmente para poblar los selectores de "responsable"
        al crear o editar un pedido (se listan solo los empleados).

        Args:
            role (str): El rol a filtrar. Valores válidos: "jefe", "empleado".

        Returns:
            list[dict]: Lista de diccionarios con los campos: id, nombre, username.
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, username FROM usuarios WHERE rol = %s", (role,)
        )
        empleados = cursor.fetchall()
        cursor.close()
        connection.close()
        return empleados

    @staticmethod
    def create(nombre, username, password, rol):
        """
        Inserta un nuevo usuario en la tabla `usuarios`.

        Args:
            nombre   (str): Nombre completo del empleado.
            username (str): Nombre de usuario único para login.
            password (str): Contraseña en texto plano (pendiente de mejorar con hashing).
            rol      (str): Rol asignado: "jefe" o "empleado".

        Returns:
            None. Lanza una excepción si el `username` ya existe (clave única en DB).
        """
        connection = get_connection()
        cursor = connection.cursor()
        query = "INSERT INTO usuarios (nombre, username, password, rol) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (nombre, username, password, rol))
        connection.commit()  # Confirmar la transacción para que el INSERT sea permanente
        cursor.close()
        connection.close()

    @staticmethod
    def update(id, nombre, username, rol, password=None):
        """
        Actualiza los datos de un usuario existente.

        Maneja dos casos:
        1. Si se proporciona `password`: Actualiza todos los campos incluyendo la contraseña.
        2. Si `password` es None (o vacío): Actualiza solo nombre, username y rol,
           dejando la contraseña sin cambios.

        Args:
            id       (int): ID del usuario a actualizar.
            nombre   (str): Nuevo nombre completo.
            username (str): Nuevo nombre de usuario.
            rol      (str): Nuevo rol ("jefe" o "empleado").
            password (str | None): Nueva contraseña. Si es None, no se actualiza.

        Returns:
            None.
        """
        connection = get_connection()
        cursor = connection.cursor()
        if password:
            # Caso 1: Se quiere cambiar también la contraseña
            query = "UPDATE usuarios SET nombre=%s, username=%s, password=%s, rol=%s WHERE id=%s"
            cursor.execute(query, (nombre, username, password, rol, id))
        else:
            # Caso 2: Actualizar todo EXCEPTO la contraseña
            query = "UPDATE usuarios SET nombre=%s, username=%s, rol=%s WHERE id=%s"
            cursor.execute(query, (nombre, username, rol, id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def delete(id):
        """
        Elimina permanentemente un usuario de la base de datos.

        PRECAUCIÓN: Esta acción no tiene reversa. La validación de negocio
        (ej. "no puedes eliminarte a ti mismo") se realiza en `EmpleadoService`
        antes de llamar a este método.

        Args:
            id (int): ID del usuario a eliminar.

        Returns:
            None.
        """
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
        connection.commit()
        cursor.close()
        connection.close()
