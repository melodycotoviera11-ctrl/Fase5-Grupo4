# DEF-F5-P1-01 – No se cargan los tres estudiantes iniciales esperados

- **Requerimiento / caso:** RF-01 / CP-RF01-03.
- **Ambiente y versión:** Windows 11, Python 3.12.2, pytest 9.1.1, base de datos SQLite temporal, commit `ee922b6` del repositorio del Grupo 6.
- **Precondiciones:** base de datos temporal nueva y ejecución inicial del sistema.
- **Datos:** carga inicial de estudiantes definida por el sistema.

## Pasos

1. Inicializar el sistema con una base de datos nueva.
2. Ejecutar el proceso de carga inicial.
3. Consultar los estudiantes almacenados.

- **Resultado esperado:** deben existir los tres estudiantes iniciales definidos por el sistema.
- **Resultado obtenido:** los tres estudiantes iniciales esperados no se encuentran cargados después de la inicialización.
- **Severidad propuesta:** Media.
- **Prioridad propuesta:** Alta.
- **Evidencia:** `evidencias/estudiantes_inicio/resultados_fase5_persona1.csv`, caso `CP-RF01-03`; `evidencias/estudiantes_inicio/salida_pytest_fase5_persona1.txt`; `evidencias/estudiantes_inicio/junit_fase5_persona1.xml`.

> La severidad y la prioridad corresponden a una propuesta del equipo evaluador y pueden revisarse durante la fase de corrección.