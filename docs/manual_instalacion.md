# Manual de Instalación y Configuración - CAMBRI

Este documento proporciona las instrucciones necesarias para desplegar la plataforma **CAMBRI** en un entorno local de desarrollo o producción.

## 1. Requisitos del Sistema

### Hardware Mínimo
- Procesador: Dual Core 2.0 GHz o superior.
- Memoria RAM: 4 GB.
- Almacenamiento: 500 MB de espacio disponible.

### Software Necesario
- **Sistema Operativo:** Windows 10/11, Linux (Ubuntu 20.04+) o macOS.
- **Lenguaje:** Python 3.12 o superior.
- **Base de Datos:** MySQL Server 8.0 o superior.
- **Navegador Web:** Google Chrome, Mozilla Firefox o Microsoft Edge (versiones actualizadas).

---

## 2. Preparación del Entorno

### 2.1 Descarga del Código
Ubíquese en la carpeta donde desea alojar el proyecto y abra una terminal.
```bash
cd d:\Camilo\APP\proyectoGrado\CAMBRI
```

### 2.2 Creación del Entorno Virtual (Recomendado)
Para aislar las dependencias del proyecto y evitar conflictos con otros paquetes de Python:

**En Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2.3 Instalación de Dependencias
Con el entorno virtual activado, instale las librerías necesarias:
```bash
pip install -r requirements.txt
```

---

## 3. Configuración de la Base de Datos

1. Abra su cliente de MySQL (Workbench, SQLyog o consola).
2. Cree una nueva base de datos llamada `cambri_db`:
   ```sql
   CREATE DATABASE cambri_db;
   ```
3. Importe el esquema de tablas (si cuenta con un archivo `.sql`) o asegúrese de que el motor esté listo para recibir conexiones.

---

## 4. Variables de Entorno (`.env`)

Cree un archivo llamado `.env` en la raíz del proyecto con la siguiente estructura. Reemplace los valores según su configuración local:

```env
SECRET_KEY=clave_segura_aleatoria
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=su_contraseña
DB_NAME=cambri_db
```

> [!IMPORTANT]
> Nunca comparta el archivo `.env` en repositorios públicos, ya que contiene credenciales sensibles.

---

## 5. Ejecución del Sistema

Para poner en marcha la plataforma, ejecute el script principal:

```bash
python run.py
```

El sistema mostrará un mensaje indicando que el servidor está corriendo en:
`http://127.0.0.1:5000/`

Abra esa dirección en su navegador para comenzar a utilizar **CAMBRI**.

---

## 6. Solución de Problemas Comunes

- **Error de conexión a la base de datos:** Verifique que el servicio de MySQL esté iniciado y que las credenciales en `.env` coincidan exactamente.
- **Módulos no encontrados:** Asegúrese de haber activado el entorno virtual (`venv`) antes de ejecutar `pip install`.
- **Puerto 5000 ocupado:** Si otro servicio usa el puerto 5000, puede cambiarlo en `run.py` o cerrar la aplicación que lo utiliza.
