# DEF-F5-P4-01 – Se registran salas con códigos equivalentes (minúsculas o espacios periféricos) y el panel no puede filtrarlas

- **Requerimiento / caso:** RF-12 / CP-RF12-03; impacto en RF-15 / CP-RF15-06.
- **Ambiente y versión:** macOS 26.6.2, Python 3.13.2, commit `ee922b6` del repositorio del Grupo 6.
- **Precondiciones:** base de datos temporal nueva con las salas iniciales (S01 a S05).
- **Datos:** códigos `s01`, `" S01 "`, `"S01 "` y `s06`.

## Pasos

1. Ejecutar `registrar_sala("s01", "Sala equivalente", 3)`.
2. Repetir con `" S01 "` y con `"S01 "`.
3. Ejecutar `consultar_salas()`.
4. Registrar la sala `s06`, crear una reservación en `s06` y consultar el panel con `consultar_panel(codigo_sala="s06")`.

- **Resultado esperado:** el código de sala es único (RF-12). Un código que solo cambia en mayúsculas o en espacios al inicio o al final debe rechazarse como duplicado, o normalizarse antes de guardar. Toda sala registrada debe poder filtrarse en el panel (RF-15).
- **Resultado obtenido:** el sistema registra `s01`, `" S01 "` y `"S01 "` como salas distintas, y la consulta queda con ocho salas: `[' S01 ', 'S01', 'S01 ', 'S02', 'S03', 'S04', 'S05', 's01']`. En el panel, el filtro convierte `s06` a `S06`, por lo que la reservación `R0001` de la sala `s06` no aparece (`resultados=[]`).
- **Causa observable en código:** `registrar_sala()` guarda el código sin `strip()` ni `upper()`. `_buscar_sala()` busca la sala con el código exacto, mientras que `_normalizar_filtros()` del panel lo convierte a mayúsculas.
- **Severidad propuesta:** Media.
- **Prioridad propuesta:** Media.
- **Evidencia:** `evidencias/salas_panel_reportes/resultados_fase5_persona4.csv`, casos `CP-RF12-03` y `CP-RF15-06`; `evidencias/salas_panel_reportes/salida_pytest_fase5_persona4.txt`; `evidencias/salas_panel_reportes/junit_fase5_persona4.xml`.

> La severidad y la prioridad corresponden a una propuesta del equipo evaluador y pueden revisarse durante la fase de corrección.
