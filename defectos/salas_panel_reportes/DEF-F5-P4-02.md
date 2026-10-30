# DEF-F5-P4-02 – Se permite registrar o modificar una sala con nombre vacío

- **Requerimiento / caso:** RF-12 y RNF-05 / CP-RF12-05.
- **Ambiente y versión:** macOS 26.6.2, Python 3.13.2, commit `ee922b6` del repositorio del Grupo 6.
- **Precondiciones:** base de datos temporal nueva con las salas iniciales.
- **Datos:** nombre `""` y nombre `"   "` (solo espacios).

## Pasos

1. Ejecutar `registrar_sala("S07", "", 3)`.
2. Ejecutar `modificar_sala("S01", "", 4, "disponible")`.
3. Repetir los pasos 1 y 2 con el nombre `"   "`.
4. Consultar las salas.

- **Resultado esperado:** el nombre es un dato del modelo de la sala que se muestra en RF-04. Una entrada inválida debe rechazarse con un mensaje y no debe producir datos incompletos (RNF-05).
- **Resultado obtenido:** las cuatro operaciones responden con éxito. La sala `S01` queda con nombre `'   '` y las salas `S07` y `S08` quedan registradas sin nombre visible.
- **Causa observable en código:** `registrar_sala()` y `modificar_sala()` validan la capacidad y el estado, pero no el nombre. La restricción `NOT NULL` de la tabla no impide cadenas vacías.
- **Severidad propuesta:** Baja.
- **Prioridad propuesta:** Media.
- **Evidencia:** `evidencias/salas_panel_reportes/resultados_fase5_persona4.csv`, caso `CP-RF12-05`; `salida_pytest_fase5_persona4.txt`; `junit_fase5_persona4.xml`.

> La severidad y la prioridad corresponden a una propuesta del equipo evaluador y pueden revisarse durante la fase de corrección.
