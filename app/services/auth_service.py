from app.models.usuario_model import UsuarioModel

class AuthService:
    @staticmethod
    def login(username, password):
        user = UsuarioModel.authenticate(username, password)
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
