param(
    [Parameter(Mandatory=$true)]
    [ValidateSet(
        "estudiantes_inicio",
        "reservaciones_creacion_reglas",
        "gestion_recurrencia",
        "salas_panel_reportes"
    )]
    [string]$Bloque,

    [Parameter(Mandatory=$true)]
    [ValidateSet(1,2,3,4)]
    [int]$Persona
)

$env:REPO_G6 = "$PWD\repo"
$env:PYTHONUTF8 = "1"

$carpetaPruebas = "pruebas\$Bloque"
$carpetaEvidencias = "evidencias\$Bloque"

if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Primero ejecute .\setup.ps1"
    exit 1
}

if (-not (Test-Path "repo")) {
    Write-Host "ERROR: No se encontro el repositorio del Grupo 6. Ejecute .\setup.ps1"
    exit 1
}

if (-not (Test-Path $carpetaPruebas)) {
    Write-Host "ERROR: No existe el bloque de pruebas $Bloque"
    exit 1
}

New-Item -ItemType Directory -Force -Path $carpetaEvidencias | Out-Null

$junit = "$carpetaEvidencias\junit_fase5_persona$Persona.xml"
$salida = "$carpetaEvidencias\salida_pytest_fase5_persona$Persona.txt"

Write-Host ""
Write-Host "=== Ejecutando bloque: $Bloque ==="
Write-Host "Persona: $Persona"
Write-Host "Version Grupo 6: ee922b6"
Write-Host ""

& ".\venv\Scripts\python.exe" -m pytest $carpetaPruebas -v --junitxml=$junit 2>&1 |
    Tee-Object -FilePath $salida

$codigo = $LASTEXITCODE

$csvTemporal = "pruebas\evidencias\resultados_fase5_persona$Persona.csv"
$csvFinal = "$carpetaEvidencias\resultados_fase5_persona$Persona.csv"

if (Test-Path $csvTemporal) {
    Move-Item -Force $csvTemporal $csvFinal
}

if (Test-Path "pruebas\evidencias") {
    $contenido = Get-ChildItem "pruebas\evidencias" -Force

    if ($contenido.Count -eq 0) {
        Remove-Item "pruebas\evidencias" -Force
    }
}

Write-Host ""
Write-Host "=== Ejecucion finalizada ==="
Write-Host "Evidencias guardadas en: $carpetaEvidencias"

exit $codigo