"""
app/infrastructure/repositories/cliente_repository.py - Repositorio de Clientes
=================================================================================
Responsabilidad: Encapsula las operaciones de base de datos sobre la tabla
`clientes`. Gestiona la creación y consulta de los clientes de la empresa.

Tabla gestionada: `clientes`
    Columnas principales: id, nombre, telefono, correo

Relación con otras tablas:
    - Un cliente puede tener MUCHOS pedidos (relación 1:N con `pedidos`).
    - La tabla `pedidos` referencia a `clientes` a través de `cliente_id`.

Lógica de cliente "nuevo" vs "existente":
    Al crear un pedido, el jefe puede elegir un cliente ya registrado
    (usando su `id`) o crear uno nuevo en ese mismo momento. Si es nuevo,
    `PedidoService` llama a `ClienteRepository.create()` para registrarlo
    y obtiene el `id` generado para asociarlo al pedido.
"""
from app.infrastructure.database import get_connection


class ClienteRepository:
    """
    Clase de repositorio estático para la tabla `clientes`.
    """

    @staticmethod
    def get_all():
        """
        Obtiene todos los clientes registrados en el sistema.

        Usado para poblar el selector "Cliente existente" en el formulario
        de creación/edición de pedidos.

        Returns:
            list[dict]: Lista de diccionarios con todos los campos de `clientes`
                        (id, nombre, telefono, correo).
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        cursor.close()
        connection.close()
        return clientes

    @staticmethod
    def create(nombre, telefono, correo):
        """
        Inserta un nuevo cliente en la base de datos.

        Se llama desde `PedidoService.create_pedido()` cuando el jefe elige
        la opción "cliente nuevo" en el formulario de creación de pedido.
        Retorna el ID del registro recién creado para poder asociarlo al pedido
        en la misma operación.

        Args:
            nombre   (str): Nombre completo o razón social del cliente.
            telefono (str): Número de teléfono de contacto.
            correo   (str): Correo electrónico de contacto.

        Returns:
            int: El `id` auto-generado por MySQL para el nuevo cliente
                 (equivalente a `LAST_INSERT_ID()`).
        """
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, correo) VALUES (%s, %s, %s)",
            (nombre, telefono, correo)
        )
        connection.commit()
        # `lastrowid` contiene el ID auto-incrementado del último INSERT
        cliente_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return cliente_id
