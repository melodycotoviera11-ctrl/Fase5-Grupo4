# Fase 5 – Grupo 4

En este repositorio se presenta todas las pruebas unitarias cruzadas de la Fase 5 del Proyecto Final de Calidad en Sistemas de Información.

El Grupo 4 evalúa el sistema desarrollado por el Grupo 6 utilizando la versión correspondiente al commit:

`ee922b6`

## Estructura

```text
Fase5-Grupo4/
├── pruebas/
│   ├── estudiantes_inicio/
│   ├── reservaciones_creacion_reglas/
│   ├── gestion_recurrencia/
│   └── salas_panel_reportes/
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
│   ├── gestion_recurrencia/
│   └── salas_panel_reportes/
│
├── requirements-pruebas.txt
├── setup.ps1
├── ejecutar_bloque.ps1
└── .gitignore
```

## Preparar el entorno

Abrir el repositorio en Visual Studio Code y utilizar una terminal de PowerShell.

Ejecutar:

```powershell
.\setup.ps1
```

Este script:

- crea el entorno virtual `venv`;
- instala las dependencias necesarias;
- clona el repositorio del Grupo 6;
- fija la versión evaluada en el commit `ee922b6`.

No es necesario activar manualmente el entorno virtual.

## Ejecutar las pruebas

### Bloque 1 – Estudiantes e inicio

```powershell
.\ejecutar_bloque.ps1 -Bloque estudiantes_inicio -Persona 1
```

### Bloque 2 – Reservaciones: creación y reglas

```powershell
.\ejecutar_bloque.ps1 -Bloque reservaciones_creacion_reglas -Persona 2
```

### Bloque 3 – Gestión y recurrencia

```powershell
.\ejecutar_bloque.ps1 -Bloque gestion_recurrencia -Persona 3
```

### Bloque 4 – Salas, panel, reportes y auditoría

```powershell
.\ejecutar_bloque.ps1 -Bloque salas_panel_reportes -Persona 4
```

## Evidencias

Después de ejecutar cada bloque, las evidencias se almacenan automáticamente en la carpeta correspondiente dentro de `evidencias/`.

Se generan archivos como:

- `junit_fase5_personaX.xml`
- `resultados_fase5_personaX.csv`
- `salida_pytest_fase5_personaX.txt`

Una prueba fallida no necesariamente representa un error en la ejecución del entorno. Puede corresponder a un defecto detectado en el sistema evaluado.

## Defectos

Los defectos encontrados deben documentarse en la carpeta correspondiente dentro de `defectos/`, incluyendo como mínimo:

- requerimiento y caso asociado;
- ambiente y versión;
- precondiciones;
- datos utilizados;
- pasos;
- resultado esperado;
- resultado obtenido;
- severidad;
- prioridad;
- evidencia.

## Trabajo con Git

Cada integrante debe trabajar en su propia rama:

```text
fase5-persona1
fase5-persona2
fase5-persona3
fase5-persona4
```

Los cambios terminados se integran posteriormente a `main`.

No se deben subir al repositorio:

```text
venv/
repo/
.pytest_cache/
__pycache__/
*.pyc
```