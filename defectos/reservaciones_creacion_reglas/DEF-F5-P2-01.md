# DEF-F5-P2-01 – Las ocurrencias de una serie recurrente no se cuentan individualmente para el máximo de tres reservaciones activas

- **Requerimiento / caso:** RN-11, relacionado con RF-14 / CP-RN11-02.
- **Ambiente y versión:** Microsoft Windows 11 Pro 10.0.26200, Python 3.14.7, commit `ee922b6` del repositorio del Grupo 6.
- **Precondiciones:** estudiante activo, salas disponibles y base de datos temporal nueva.
- **Datos:** serie recurrente de 3 ocurrencias futuras para el mismo estudiante y una reservación individual adicional futura.

## Pasos

1. Crear una serie recurrente de 3 ocurrencias.
2. Confirmar que existen 3 reservaciones activas presentes o futuras para el estudiante.
3. Intentar crear una cuarta reservación activa para el mismo estudiante.

- **Resultado esperado:** la cuarta reservación se rechaza porque RN-11 permite como máximo tres reservaciones activas presentes o futuras.
- **Resultado obtenido:** la serie se creó correctamente con `R0001`, `R0002` y `R0003`. Posteriormente, el sistema también permitió crear la reservación individual `R0004`, dejando cuatro reservaciones activas para el mismo estudiante.
- **Causa observable en código:** `_contar_reservaciones_vigentes()` agrupa las ocurrencias que comparten un mismo `serie_id` como una sola unidad al calcular el límite de reservaciones activas.
- **Severidad propuesta:** Media.
- **Prioridad propuesta:** Alta.
- **Evidencia:** `evidencias/reservaciones_creacion_reglas/resultados_fase5_persona2.csv`, caso `CP-RN11-02`; `evidencias/reservaciones_creacion_reglas/salida_pytest_fase5_persona2.txt`; `evidencias/reservaciones_creacion_reglas/junit_fase5_persona2.xml`.

> La severidad y la prioridad corresponden a una propuesta del equipo evaluador y pueden revisarse durante la fase de corrección.