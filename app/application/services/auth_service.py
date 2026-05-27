"""
app/application/services/auth_service.py - Servicio de Autenticación
======================================================================
Responsabilidad: Contiene la lógica de negocio del proceso de inicio
de sesión. Actúa como intermediario entre el controlador (Blueprint `auth`)
y el repositorio de usuarios.

¿Por qué tener un Service si solo llama al Repository?
    La capa de Servicio es el lugar correcto para:
    - Agregar reglas de negocio (ej. bloquear usuarios después de 3 intentos fallidos).
    - Transformar datos (ej. normalizar el username a minúsculas antes de buscar).
    - Retornar un resultado estandarizado (dict con "success" y datos o "error"),
      desacoplando al controlador de la estructura interna del repositorio.

Flujo de autenticación:
    1. El Blueprint `auth` recibe el POST del formulario de login.
    2. Extrae `username` y `password` del formulario.
    3. Llama a `AuthService.login(username, password)`.
    4. AuthService delega la verificación a `UsuarioRepository.authenticate()`.
    5. Si el usuario existe, retorna un dict con `success=True` y los datos
       de sesión necesarios (id, username, rol).
    6. El Blueprint guarda esos datos en `flask.session` y redirige al Dashboard.
"""
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class AuthService:
    """
    Servicio de autenticación de usuarios.

    Encapsula la lógica de login y retorna un resultado estandarizado
    que el controlador puede consumir directamente sin conocer los
    detalles de la base de datos.
    """

    @staticmethod
    def login(username, password):
        """
        Valida las credenciales de un usuario y prepara los datos de sesión.

        Delega la verificación de credenciales al repositorio de usuarios.
        Si las credenciales son correctas, retorna los datos necesarios para
        crear la sesión de Flask. Si son incorrectas, retorna un error descriptivo.

        Args:
            username (str): Nombre de usuario ingresado en el formulario.
            password (str): Contraseña ingresada en el formulario.

        Returns:
            dict: Resultado del intento de login. Dos posibles estructuras:

            Éxito:
                {
                    "success": True,
                    "user_id": int,       # ID del usuario para almacenar en session
                    "username": str,      # Nombre de usuario para mostrar en la UI
                    "rol": str            # "jefe" o "empleado" para control de acceso
                }

            Fallo:
                {
                    "success": False,
                    "error": str          # Mensaje de error para mostrar al usuario
                }
        """
        # Delegar la verificación de credenciales al repositorio
        user = UsuarioRepository.authenticate(username, password)

        if user:
            # Credenciales correctas: preparar datos para la sesión de Flask
            return {
                "success": True,
                "user_id": user["id"],
                "username": user["username"],
                "rol": user["rol"]
            }

        # Credenciales incorrectas: retornar error genérico
        # (no especificar si el error es el username o la contraseña, por seguridad)
        return {
            "success": False,
            "error": "Usuario o contraseña incorrectos"
        }
