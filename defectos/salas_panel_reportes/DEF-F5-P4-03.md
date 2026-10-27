# DEF-F5-P4-03 – La auditoría de series recurrentes no identifica las reservaciones afectadas

- **Requerimiento / caso:** RF-17 (relacionado con RF-14) / CP-RF17-07.
- **Ambiente y versión:** macOS 26.6.2, Python 3.13.2, commit `ee922b6` del repositorio del Grupo 6.
- **Precondiciones:** estudiante activo `A001234567`, sala `S01` disponible y base de datos temporal nueva.
- **Datos:** serie semanal de 3 ocurrencias, 1 hora, 2 personas.

## Pasos

1. Crear la serie con `crear_reservaciones_recurrentes(...)`. Se generan `R0001`, `R0002` y `R0003`.
2. Cancelar las ocurrencias futuras desde `R0002` con `cancelar_ocurrencias_futuras("R0002")`.
3. Consultar la tabla de auditoría.

- **Resultado esperado:** según RF-17, cada registro incluye el identificador afectado. Debe poder rastrearse en el historial cuáles reservaciones se crearon y cuáles se cancelaron.
- **Resultado obtenido:** se registran solo dos eventos, ambos con `entidad = 'reservacion'` y `entidad_id = 'SR0001'` (el código de la serie). El detalle indica la cantidad de ocurrencias, pero no sus ID. Al buscar `R0002` o `R0003` en la auditoría no aparece ningún evento.
- **Causa observable en código:** `crear_reservaciones_recurrentes()` y `cancelar_ocurrencias_futuras()` llaman una sola vez a `registrar_evento()` con `serie_id` como identificador.
- **Severidad propuesta:** Baja.
- **Prioridad propuesta:** Baja.
- **Evidencia:** `evidencias/salas_panel_reportes/resultados_fase5_persona4.csv`, caso `CP-RF17-07`; `salida_pytest_fase5_persona4.txt`; `junit_fase5_persona4.xml`.

> Hallazgo de interpretación: el equipo desarrollador puede argumentar que el código de serie es suficiente. Si lo rechaza, debe justificarlo en la Fase 6.
