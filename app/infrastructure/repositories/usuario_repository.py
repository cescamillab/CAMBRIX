from app.infrastructure.database import get_connection

class UsuarioRepository:
    @staticmethod
    def authenticate(username, password):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user

    @staticmethod
    def get_all():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, username, rol FROM usuarios")
        empleados = cursor.fetchall()
        cursor.close()
        connection.close()
        return empleados

    @staticmethod
    def get_by_role(role):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, username FROM usuarios WHERE rol = %s", (role,))
        empleados = cursor.fetchall()
        cursor.close()
        connection.close()
        return empleados

    @staticmethod
    def create(nombre, username, password, rol):
        connection = get_connection()
        cursor = connection.cursor()
        query = "INSERT INTO usuarios (nombre, username, password, rol) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (nombre, username, password, rol))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def update(id, nombre, username, rol, password=None):
        connection = get_connection()
        cursor = connection.cursor()
        if password:
            query = "UPDATE usuarios SET nombre=%s, username=%s, password=%s, rol=%s WHERE id=%s"
            cursor.execute(query, (nombre, username, password, rol, id))
        else:
            query = "UPDATE usuarios SET nombre=%s, username=%s, rol=%s WHERE id=%s"
            cursor.execute(query, (nombre, username, rol, id))
        connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def delete(id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
        connection.commit()
        cursor.close()
        connection.close()
