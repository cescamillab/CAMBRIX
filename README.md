# CAMBRIX (Proyecto Chamba)

Este es un dashboard analítico y sistema de gestión desarrollado en Python usando Flask. 

## Requisitos Previos

1. **Python 3.8+** instalado en tu sistema.
2. **MySQL Server** en ejecución.

## Configuración del Entorno

1. Clona este repositorio o navega hasta la carpeta del proyecto:
   ```bash
   cd d:\Camilo\APP\proyectoGrado\CAMBRI
   ```

2. Crea y activa un entorno virtual **(Opcional, pero recomendado para evitar conflictos de paquetes)**:
   Si decides no usar un entorno virtual, puedes omitir este paso y pasar directamente al paso 3.

   **En Windows:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
   **En Linux/Mac:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración de Base de Datos y Variables de Entorno

Asegúrate de que exista un archivo `.env` en la raíz del proyecto (junto a `run.py`). Debe contener la configuración de conexión a la base de datos MySQL y la clave secreta de la aplicación:

```env
SECRET_KEY=clave_super_secreta_123
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=1234
DB_NAME=cambri_db
```

**Nota:** 
- Asegúrate de que tu servidor MySQL esté encendido y tengas las credenciales correctas.
- Debes crear la base de datos llamada `cambri_db` en tu motor de MySQL antes de ejecutar la aplicación.

## Documentación del Proyecto

Para una comprensión profunda del sistema, consulte los siguientes manuales detallados:

- [Manual de Usuario](docs/manual_usuario.md): Guía para el personal operativo.
- [Manual Técnico](docs/manual_tecnico.md): Arquitectura, base de datos y tecnologías.
- [Manual de Instalación y Configuración](docs/manual_instalacion.md): Pasos para desplegar el sistema.
- [Manual de Mantenimiento](docs/manual_mantenimiento.md): Procedimientos de respaldo y actualización.
- [Manual de Pruebas](docs/manual_pruebas.md): Protocolos de validación funcional.

---

## Ejecución

Para iniciar el servidor de desarrollo, ejecuta el siguiente comando estando en la raíz del proyecto (y con el entorno virtual activado):

```bash
python run.py
```

La aplicación estará disponible en tu navegador en la dirección:
`http://127.0.0.1:5000/`
