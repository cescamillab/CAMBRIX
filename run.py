"""
run.py - Punto de Entrada de la Aplicación CAMBRIX
====================================================
Este es el archivo que se ejecuta para iniciar el servidor web de Flask.

Flujo:
1. Importa la función factoría `create_app` desde el paquete `app`.
2. Llama a `create_app()` que configura Flask, registra todos los Blueprints
   y aplica la configuración del entorno (.env).
3. Lanza el servidor en modo DEBUG cuando se ejecuta directamente
   (nunca en producción).

Uso:
    python run.py

El servidor levanta en: http://127.0.0.1:5000/

ADVERTENCIA: `debug=True` NUNCA debe usarse en producción. En producción,
usar un servidor WSGI como Gunicorn o Waitress.
"""
from app import create_app

# Crea la instancia de la aplicación Flask usando el patrón factoría (Application Factory).
# Esto permite crear múltiples instancias con distintas configuraciones (ej. para testing).
app = create_app()

if __name__ == "__main__":
    # Solo se ejecuta si el archivo se corre directamente (no si se importa como módulo).
    # debug=True activa el reloader automático y el debugger interactivo de Flask.
    app.run(debug=True)
