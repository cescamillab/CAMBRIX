# Manual de Pruebas - CAMBRI

Este documento describe el protocolo de pruebas para asegurar que todas las funcionalidades de **CAMBRI** operen correctamente antes de una entrega o actualización.

## 1. Casos de Prueba Funcionales

### CP-01: Autenticación de Usuarios
- **Entrada:** Usuario y contraseña válidos.
- **Resultado Esperado:** Redirección al Dashboard y visualización del Sidebar.
- **Entrada:** Usuario o contraseña inválidos.
- **Resultado Esperado:** Mensaje de error "Credenciales inválidas" y permanencia en el login.

### CP-02: Flujo de Pedidos
1. **Creación:** Llenar formulario de pedido -> Verificar que aparezca en la lista.
2. **Edición:** Cambiar descripción o valor -> Verificar actualización en el detalle.
3. **Estado:** Cambiar de "Pendiente" a "Terminado" -> Verificar que el gráfico del Dashboard se actualice.

### CP-03: Gestión de Inventario
- **Entrada:** Registro de movimiento de "Entrada" de 10 unidades.
- **Resultado Esperado:** El stock actual del material debe aumentar en 10.
- **Validación:** Intentar registrar una salida mayor al stock disponible (si el sistema tiene la validación activa).

### CP-04: Reportes
- **Acción:** Seleccionar rango de fechas y descargar PDF de Pedidos.
- **Resultado Esperado:** Archivo PDF generado correctamente con el logo de Cambri (si existe) y datos filtrados.

---

## 2. Pruebas de Integración
- **Inventario vs Producción:** Al añadir materiales en el módulo de Producción, verifique que el stock en el módulo de Inventario disminuya automáticamente.
- **Dashboard vs Base de Datos:** Verifique que los valores de facturación total coincidan con la suma manual de los pedidos marcados como terminados o en proceso.

---

## 3. Pruebas de Interfaz (UX/UI)
- **Responsividad:** Reducir el tamaño de la ventana del navegador. El sidebar debe colapsar o adaptarse y las tarjetas deben apilarse verticalmente.
- **Tooltips:** Pasar el mouse sobre los iconos de acción en Inventario -> Debe aparecer el texto descriptivo.
- **Gráficos:** Los gráficos de Chart.js deben cargar con sus animaciones iniciales y mostrar datos al pasar el mouse.

---

## 4. Registro de Resultados
Se recomienda usar una tabla para documentar cada ciclo de pruebas:

| ID Prueba | Fecha | Responsable | Estado (Pasa/Falla) | Observaciones |
| :--- | :--- | :--- | :--- | :--- |
| CP-01 | 2026-04-28 | QA | Pasa | - |
| CP-02 | 2026-04-28 | QA | Pasa | - |  
