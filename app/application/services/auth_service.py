from app.infrastructure.repositories.usuario_repository import UsuarioRepository

class AuthService:
    @staticmethod
    def login(username, password):
        user = UsuarioRepository.authenticate(username, password)
        if user:
            return {
                "success": True,
                "user_id": user["id"],
                "username": user["username"],
                "rol": user["rol"]
            }
        return {
            "success": False,
            "error": "Usuario o contraseña incorrectos"
        }
