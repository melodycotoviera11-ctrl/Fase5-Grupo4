# DEF-F7-P2-01 – La creación de reservaciones no normaliza la hora y permite traslapes cuando se usa 9:00 en lugar de 09:00

- **Requerimiento / caso:** RN-09 y RF-05 / CP-F7P2-04.
- **Ambiente y versión:** Microsoft Windows, Python 3.15.2, pytest 9.1.1, commit `92e1fd8` de la rama `dev-vega` del repositorio del Grupo 6.
- **Precondiciones:** estudiantes activos, sala S01 disponible y base de datos temporal nueva.
- **Datos:** reservación existente en S01 de 09:00 a 10:00 (fecha futura); nueva solicitud en S01 para la misma fecha con hora `9:00`, duración 1 hora y 2 personas.

## Pasos

1. Crear con `crear_reservacion()` una reservación en S01 a las `09:00` por 1 hora.
2. Consultar la disponibilidad de S01 a las `9:00` por 1 hora. El sistema responde que no está disponible (la corrección de BUG-P1-DIS-01 de RF-08 funciona).
3. Crear con `crear_reservacion()` otra reservación en S01, misma fecha, a las `9:00` por 1 hora, con otro estudiante activo.

- **Resultado esperado:** la segunda solicitud se rechaza porque se traslapa con la reservación de 09:00 a 10:00 (RN-09), igual que lo informa la consulta de disponibilidad. La hora se guarda normalizada como `09:00`.
- **Resultado obtenido:** el sistema crea la segunda reservación y guarda la hora como `9:00`. Quedan dos reservaciones activas en S01 para la misma franja (`09:00` y `9:00`). La consulta de disponibilidad y la creación dan respuestas contradictorias para el mismo dato.
- **Causa observable en código:** `_preparar_datos_reservacion()` guarda `hora_inicio.strip()` sin normalizar a `HH:MM`, y `_buscar_conflicto()` compara las horas como texto. Como `"9:00"` es mayor que `"09:00"` en una comparación de texto, el traslape no se detecta. La normalización que se agregó en `consultar_disponibilidad()` no se aplicó a la creación. El mismo comportamiento se observó en pruebas exploratorias con reservaciones recurrentes.
- **Alcance:** desde la interfaz gráfica las horas se eligen de una lista fija con formato `HH:00`, por lo que el defecto se presenta al usar la capa de servicio directamente.
- **Severidad propuesta:** Media.
- **Prioridad propuesta:** Media.
- **Evidencia:** `evidencias/reservaciones_creacion_reglas/resultados_fase7_persona2.csv`, caso `CP-F7P2-04`; `evidencias/reservaciones_creacion_reglas/salida_pytest_fase7_persona2.txt`; `evidencias/reservaciones_creacion_reglas/junit_fase7_persona2.xml`.

> La severidad y la prioridad corresponden a una propuesta del equipo evaluador y pueden revisarse durante la fase de corrección.
