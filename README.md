# Grupo 4 – Pruebas cruzadas del sistema de reservación de salas (Fases 5 y 7)

En este repositorio están las pruebas que el Grupo 4 ejecutó como equipo evaluador sobre el sistema de reservación de salas del Grupo 6, para el Proyecto Final de Calidad en Sistemas de Información.

- **Fase 5. Pruebas unitarias cruzadas.** Primera evaluación del sistema.
- **Fase 7. Integración y regresión.** Verificación de las correcciones y rechazos que el Grupo 6 informó en su Fase 6, repetición de la regresión de Fase 5 y pruebas de integración entre módulos.

## Versiones evaluadas

| Fase | Repositorio del Grupo 6 | Versión |
|---|---|---|
| Fase 5 | `github.com/AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026` | commit `ee922b6` |
| Fase 7 | `github.com/AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026`, rama `dev-vega` | commit `92e1fd8` |

El script `setup.ps1` deja el código del Grupo 6 fijo en `92e1fd8`, que es la versión de Fase 7.

## Estructura

```text
Fase5-Grupo4/
├── pruebas/
│   ├── estudiantes_inicio/            # Área 1
│   ├── reservaciones_creacion_reglas/ # Área 2
│   ├── gestion_recurrencia/           # Área 3
│   ├── fase7_persona3/                # Área 3, pruebas adicionales de Fase 7
│   └── salas_panel_reportes/          # Área 4
│
├── evidencias/
│   ├── estudiantes_inicio/
│   ├── reservaciones_creacion_reglas/
│   ├── gestion_recurrencia/
│   └── salas_panel_reportes/
│
├── defectos/
│   ├── estudiantes_inicio/
│   ├── reservaciones_creacion_reglas/
│   └── salas_panel_reportes/
│
├── requirements-pruebas.txt
├── setup.ps1
├── ejecutar_bloque.ps1
└── .gitignore
```

## Requisitos

- Git.
- Python 3.12 o superior. Las ejecuciones de Fase 7 se hicieron con Python 3.12.1, 3.13.2 y 3.15.2.
- PowerShell en Windows para usar los scripts `setup.ps1` y `ejecutar_bloque.ps1`. En macOS o Linux se pueden usar los comandos manuales de más abajo.

Las dependencias de las pruebas están en `requirements-pruebas.txt` (pytest 9.1.1 y tzdata).

## Preparar el entorno (Windows)

Abrir el repositorio en Visual Studio Code y usar una terminal de PowerShell.

```powershell
.\setup.ps1
```

El script hace lo siguiente.

- Crea el entorno virtual `venv`.
- Instala las dependencias de `requirements-pruebas.txt`.
- Clona el repositorio del Grupo 6 en la carpeta `repo/`.
- Fija la versión evaluada en el commit `92e1fd8`.

No hace falta activar el entorno virtual a mano.

## Ejecutar la regresión de Fase 7 (Windows)

Cada área se ejecuta con `ejecutar_bloque.ps1`.

```powershell
.\ejecutar_bloque.ps1 -Bloque estudiantes_inicio -Persona 1
.\ejecutar_bloque.ps1 -Bloque reservaciones_creacion_reglas -Persona 2
.\ejecutar_bloque.ps1 -Bloque gestion_recurrencia -Persona 3
.\ejecutar_bloque.ps1 -Bloque salas_panel_reportes -Persona 4
```

Cada ejecución guarda sus resultados en `evidencias/<área>/` con estos nombres.

- `junit_fase7_personaX.xml`
- `salida_pytest_fase7_personaX.txt`
- `resultados_fase7_personaX.csv` (en las áreas cuyo `conftest.py` genera el resumen por caso)

Una prueba fallida no significa que el entorno falló. Puede corresponder a un defecto del sistema evaluado. Los fallos esperados están explicados en la tabla de resultados.

### Pruebas adicionales de Fase 7 del área 3

Las pruebas adicionales de gestión y recurrencia están en una carpeta aparte y se ejecutan así.

```powershell
$env:REPO_G6 = "$PWD\repo"
$env:PYTHONUTF8 = "1"
.\venv\Scripts\python.exe -m pytest pruebas\fase7_persona3 -v --junitxml=evidencias\gestion_recurrencia\junit_fase7_persona3_adicionales.xml
```

## Ejecución manual (macOS o Linux)

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r requirements-pruebas.txt
git clone https://github.com/AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026.git repo
git -C repo checkout 92e1fd8

export REPO_G6="$PWD/repo"
export PYTHONUTF8=1
./venv/bin/python -m pytest pruebas/salas_panel_reportes -v --junitxml=evidencias/salas_panel_reportes/junit_fase7_persona4.xml
```

Para otra área se cambia la carpeta de `pruebas/` y el nombre del archivo XML.

## Pruebas agregadas en Fase 7

| Área | Archivo | Casos |
|---|---|---|
| 1. Estudiantes e inicio | `pruebas/estudiantes_inicio/test_bug_ini02.py` | Verificación de BUG-INI-02 |
| 1. Estudiantes e inicio | `pruebas/estudiantes_inicio/test_integracion_fase7.py` | Integración de estudiantes y reservaciones |
| 2. Creación y reglas | `pruebas/reservaciones_creacion_reglas/test_fase7_persona2.py` | CP-F7P2-01 a CP-F7P2-04 |
| 3. Gestión y recurrencia | `pruebas/fase7_persona3/test_fase7_persona3.py` | CP-F7P3-01 a CP-F7P3-03 |
| 4. Salas, panel, reportes y auditoría | `pruebas/salas_panel_reportes/test_fase7_persona4.py` | CP-F7P4-01 a CP-F7P4-07 |

### Ajuste de los `conftest.py`

En la versión `92e1fd8` el Grupo 6 corrigió BUG-INI-01 y la inicialización ya carga los tres estudiantes base. Los `conftest.py` de Fase 5 los insertaban otra vez, lo que producía errores de carné duplicado antes de ejecutar los casos. En Fase 7 se ajustaron solo los `conftest.py` de las pruebas para usar los estudiantes existentes y verificar sus datos. No se modificó el código del Grupo 6. La salida de esa primera corrida del área 3 se conserva en `evidencias/gestion_recurrencia/salida_primera_corrida_persona3.txt`.

## Resultados

| Área | Fase 5 | Fase 7 (regresión) | Pruebas adicionales de Fase 7 |
|---|---|---|---|
| 1. Estudiantes e inicio | 24/25 | 25/25 | 2 aprobadas |
| 2. Creación y reglas | 31/32 | 31/32 (falla CP-RN11-02, DEF-F5-P2-01) | 3 de 4 aprobadas (falla CP-F7P2-04, DEF-F7-P2-01) |
| 3. Gestión y recurrencia | 25/25 | 25/25 | 3 aprobadas |
| 4. Salas, panel, reportes y auditoría | 31/35 | 31/35 (DEF-F5-P4-01, 02 y 03) | 5 de 7 aprobadas |
| **Total de regresión** | | **112/117 (95,7 %)** | |

Las evidencias de Fase 5 se conservan con los nombres `*_fase5_personaX.*` y las de Fase 7 con `*_fase7_personaX.*`.

## Defectos

Cada defecto está en `defectos/<área>/` con los campos de la sección 15.2 del enunciado, es decir requerimiento, ambiente y versión, precondiciones y datos, pasos, resultado esperado, resultado obtenido, severidad, prioridad y evidencia.

| ID | Área | Estado en Fase 7 |
|---|---|---|
| DEF-F5-P1-01 | 1 | Corregido |
| DEF-F5-P2-01 | 2 | Abierto |
| DEF-F7-P2-01 | 2 | Nuevo en Fase 7, abierto |
| DEF-F5-P4-01 | 4 | Abierto (corrección parcial) |
| DEF-F5-P4-02 | 4 | Abierto |
| DEF-F5-P4-03 | 4 | Abierto |

El seguimiento del área 4 está en `defectos/salas_panel_reportes/SEGUIMIENTO-F7-P4.md`.

## Trabajo con Git

Cada integrante trabajó en su propia rama y los cambios se integraron a `main` con Pull Requests.

| Área | Rama de Fase 5 | Rama de Fase 7 |
|---|---|---|
| 1 | `fase5-persona1` | `fase7-persona1-estudiantes` |
| 2 | `fase5-persona2` | `fase7-persona2-reservaciones` |
| 3 | `fase5-persona3` | `fase7-persona3-gestion` |
| 4 | `fase5-persona4` | `fase7-persona4-salas` |

No se suben al repositorio estas carpetas y archivos.

```text
venv/
repo/
.pytest_cache/
__pycache__/
*.pyc
```
