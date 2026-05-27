"""
app/core/config.py - Configuración Central de la Aplicación
=============================================================
Este módulo define la clase `Config`, que actúa como contenedor
de todas las variables de configuración que Flask necesita.

Patrón utilizado:
    Se usa el patrón "Config Object" de Flask. En lugar de pasar
    valores directamente a `app.config`, se define una clase y se
    pasa con `app.config.from_object(Config)`. Esto centraliza
    la configuración y facilita tener múltiples entornos
    (ej. DevelopmentConfig, ProductionConfig).

Fuente de los valores:
    Todas las variables se leen del archivo `.env` en la raíz del
    proyecto, gracias a la librería `python-dotenv`. Esto garantiza
    que ningún dato sensible (contraseñas, claves secretas) esté
    escrito directamente en el código fuente.

Variables de Entorno Requeridas (en el archivo .env):
    - SECRET_KEY: Clave criptográfica para firmar las sesiones de Flask.
      Debe ser una cadena larga, aleatoria y secreta.
    - DB_HOST:     Host del servidor MySQL (ej. "localhost").
    - DB_USER:     Nombre de usuario de MySQL (ej. "root").
    - DB_PASSWORD: Contraseña del usuario de MySQL.
    - DB_NAME:     Nombre de la base de datos (ej. "cambri_db").
"""
import os
from dotenv import load_dotenv

# Carga las variables definidas en el archivo `.env` al entorno del sistema operativo.
# Esto hace que `os.getenv(...)` pueda leerlas como si fueran variables de entorno reales.
# Si el archivo .env no existe, no lanza error; las variables simplemente serán None.
load_dotenv()


class Config:
    """
    Clase de configuración que Flask carga con `app.config.from_object(Config)`.

    Cada atributo de clase se convierte en una clave en el diccionario `app.config`.
    Flask lee algunas claves especiales como SECRET_KEY de forma automática.
    Las claves de base de datos (DB_*) son leídas manualmente por `database.py`.
    """

    # SECRET_KEY: Usada por Flask para firmar criptográficamente las cookies de sesión.
    # Si esta clave cambia, todas las sesiones activas se invalidan automáticamente.
    # NUNCA hardcodear este valor en el código; siempre desde el .env.
    SECRET_KEY = os.getenv("SECRET_KEY")

    # DB_HOST: Dirección del servidor de base de datos.
    # En desarrollo local es "localhost". En producción sería la IP o dominio del servidor DB.
    DB_HOST = os.getenv("DB_HOST")

    # DB_USER: Usuario con permisos sobre la base de datos `cambri_db`.
    DB_USER = os.getenv("DB_USER")

    # DB_PASSWORD: Contraseña del usuario de base de datos.
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # DB_NAME: Nombre exacto de la base de datos MySQL a la que se conecta la aplicación.
    DB_NAME = os.getenv("DB_NAME")
