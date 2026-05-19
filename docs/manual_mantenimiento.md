# Manual de Mantenimiento - CAMBRI

Este documento define las actividades necesarias para garantizar la continuidad y estabilidad de la plataforma **CAMBRI**.

## 1. Copias de Seguridad (Backups)

### 1.1 Base de Datos (MySQL)
Es fundamental realizar respaldos periódicos de la base de datos `cambri_db`.
- **Manual:** Use MySQL Workbench o el comando `mysqldump`:
  ```bash
  mysqldump -u root -p cambri_db > backup_fecha.sql
  ```
- **Frecuencia Recomendada:** Diaria para entornos de alta producción, semanal para entornos estándar.

---

## 2. Gestión de Logs y Errores
El servidor Flask muestra errores en la terminal durante la ejecución en modo desarrollo.
- Para producción, se recomienda redirigir la salida a un archivo:
  ```bash
  python run.py > logs_produccion.log 2>&1
  ```
- Revise periódicamente este archivo para identificar intentos de acceso fallidos o errores de base de datos.

---

## 3. Actualización de Dependencias
Las librerías de Python pueden recibir parches de seguridad. Para actualizar:
1. Active el entorno virtual.
2. Ejecute:
   ```bash
   pip list --outdated
   pip install --upgrade [nombre_paquete]
   ```
3. Después de actualizar, genere un nuevo archivo de requisitos:
   ```bash
   pip freeze > requirements.txt
   ```

---

## 4. Limpieza de Datos Temporales
- **Cache del Navegador:** Si realiza cambios en el archivo `style.css`, los usuarios podrían necesitar presionar `Ctrl + F5` para ver los cambios.
- **Archivos Estáticos:** Elimine imágenes o logos antiguos que ya no se utilicen en la carpeta `app/static/img/` para ahorrar espacio.

---

## 5. Escalabilidad del Sistema

### Agregar nuevos Usuarios
Actualmente se realiza directamente en la base de datos o a través de un módulo administrativo (si se implementa en el futuro). Asegúrese de asignar el rol correcto (`jefe` o `empleado`).

### Nuevas Gráficas
Para agregar nuevas métricas al Dashboard:
1. Cree la consulta SQL en `app/dashboard/routes.py`.
2. Pase los datos al template `dashboard.html`.
3. Configure un nuevo objeto `Chart` en el bloque de JavaScript del template.
