# Seguimiento de Fase 7 – Persona 4 (salas, panel, reportes y auditoría)

- **Versión evaluada:** commit `92e1fd8` del repositorio del Grupo 6.
- **Pruebas:** `pruebas/salas_panel_reportes/` (35 casos de regresión de Fase 5 y 7 casos adicionales `CP-F7P4-01` a `CP-F7P4-07`).
- **Evidencia:** `evidencias/salas_panel_reportes/resultados_fase7_persona4.csv`, `salida_pytest_fase7_persona4.txt` y `junit_fase7_persona4.xml`.

## Correcciones y rechazo informados por el Grupo 6

| ID | Decisión del Grupo 6 | Caso de Fase 7 | Resultado | Estado |
|---|---|---|---|---|
| BUG-P1-SAL-01 | Corregido | CP-F7P4-01 | Con S01 registrada, `s01` se rechaza con mensaje; no cambian las salas ni la auditoría. | Corrección verificada |
| BUG-P5-REP-01 | Corregido | CP-F7P4-02 | Con fallos simulados al escribir encabezados, al escribir filas y al reemplazar el destino, y con un destino que es una carpeta, no queda ningún `.tmp` y el CSV anterior conserva sus bytes. | Corrección verificada |
| BUG-PAN-01 | Rechazado | CP-F7P4-03 y CP-F7P4-04 | Tras cancelar la serie desde su primera ocurrencia, S01 muestra 0 reservaciones activas y no hay próximas, en el servicio, en el controlador y en la ventana real del panel. | Rechazo aceptado |

## Defectos y observación de Fase 5 (Grupo 4)

### DEF-F5-P4-01 – Códigos de sala equivalentes y filtro del panel: **Abierto (corrección parcial)**

- **Casos:** CP-RF12-03, CP-RF15-06 y CP-F7P4-07.
- **Lo corregido:** un código que solo difiere en mayúsculas de uno existente se rechaza (`s01` con `S01` registrada).
- **Lo que persiste:**
  1. `" S01 "` y `"S01 "` se registran como salas distintas; la consulta queda con 7 salas (`[' S01 ', 'S01', 'S01 ', 'S02', 'S03', 'S04', 'S05']`).
  2. Un código nuevo en minúscula (`s06`) se guarda tal cual. El panel convierte el filtro a `S06` y no muestra sus reservaciones.
  3. Con `s06` registrada, el sistema da respuestas contradictorias: registrar `S06` responde «El código de sala ya se encuentra registrado.», pero reservar o consultar disponibilidad en `S06` responde «La sala especificada no existe.».
- **Causa observable:** `registrar_sala()` compara el código con `COLLATE NOCASE`, pero no aplica `strip()` ni `upper()` antes de guardar; `_buscar_sala()` y las demás consultas siguen comparando el texto exacto.
- **Severidad / prioridad:** se mantienen Media / Media.

### DEF-F5-P4-02 – Sala con nombre vacío: **Abierto**

- **Caso:** CP-RF12-05. `registrar_sala()` y `modificar_sala()` siguen aceptando `""` y `"   "` como nombre.
- **Severidad / prioridad:** se mantienen Baja / Media.

### DEF-F5-P4-03 – Auditoría de series sin identificadores de reservación: **Abierto**

- **Caso:** CP-RF17-07. Al crear la serie (R0001 a R0003) y cancelar desde R0002 se registran dos eventos con `entidad_id = 'SR0001'`; las reservaciones afectadas no aparecen.
- **Severidad / prioridad:** se mantienen Baja / Baja.

### OBS-F5-P4-01 – Interfaz sin gestión de salas: **Persiste**

- **Caso:** CP-F7P4-05. El menú ofrece «Generar reporte CSV…», «Salir», «Nueva recurrencia…» y «Auditoría…». El controlador no expone `registrar_sala()` ni `modificar_sala()`, y ningún archivo de `src/view` las usa.

## Defectos nuevos

No se registran defectos nuevos. La contradicción entre registro y reservación del punto 3 de DEF-F5-P4-01 se documenta dentro de ese defecto porque tiene la misma causa (códigos de sala sin normalizar).
