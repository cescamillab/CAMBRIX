from app.infrastructure.database import get_connection

class ClienteRepository:
    @staticmethod
    def get_all():
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        cursor.close()
        connection.close()
        return clientes

    @staticmethod
    def create(nombre, telefono, correo):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, correo) VALUES (%s, %s, %s)",
            (nombre, telefono, correo)
        )
        connection.commit()
        cliente_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return cliente_id
