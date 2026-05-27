"""
app/infrastructure/database.py - Conector a la Base de Datos MySQL
====================================================================
Este módulo provee la función `get_connection()`, que es el único
punto de acceso a la base de datos en toda la aplicación.

Patrón utilizado: "Connection per Request" (Conexión por petición).
    En lugar de mantener un pool de conexiones permanentes, se abre
    una nueva conexión a MySQL al inicio de cada operación y se cierra
    al finalizar. Este patrón es simple y suficiente para aplicaciones
    de tamaño mediano.

    Ventajas:
    - Simple de entender y depurar.
    - No requiere configuración de pool de conexiones.

    Desventajas:
    - Menor rendimiento bajo alta concurrencia que un pool de conexiones.
    - Si se olvida cerrar la conexión, puede agotar el límite de
      conexiones del servidor MySQL. (Siempre usar `cursor.close()`
      y `connection.close()` en los repositorios).

IMPORTANTE: Esta función SOLO puede ser llamada dentro de un contexto
de aplicación Flask activo (dentro de una petición HTTP o con
`with app.app_context():`), porque depende de `current_app.config`.
"""
import mysql.connector
from flask import current_app


def get_connection():
    """
    Crea y retorna una nueva conexión activa a la base de datos MySQL.

    Lee los parámetros de conexión (host, usuario, contraseña, base de datos)
    desde la configuración de Flask, que a su vez los obtiene del archivo `.env`
    a través de `app/core/config.py`.

    Returns:
        mysql.connector.connection.MySQLConnection: Un objeto de conexión
        activa a MySQL, listo para crear cursores y ejecutar consultas.

    Raises:
        mysql.connector.Error: Si los parámetros de conexión son incorrectos
        o el servidor MySQL no está disponible, lanza una excepción. Esto
        provocará un error 500 en la aplicación si no se captura.

    Ejemplo de uso en un repositorio:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM materiales")
        resultados = cursor.fetchall()
        cursor.close()
        connection.close()  # SIEMPRE cerrar la conexión al terminar
        return resultados
    """
    connection = mysql.connector.connect(
        host=current_app.config["DB_HOST"],         # Ej: "localhost"
        user=current_app.config["DB_USER"],         # Ej: "root"
        password=current_app.config["DB_PASSWORD"], # Ej: "mi_password"
        database=current_app.config["DB_NAME"]      # Ej: "cambri_db"
    )
    return connection
