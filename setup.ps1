$ErrorActionPreference = "Stop"

$repoUrl = "https://github.com/AlejandroPenarandaSoto/proyecto-qa-II-semestre-2026.git"
$commitGrupo6 = "ee922b6"

Write-Host "=== Configurando entorno de pruebas de Fase 5 ==="

if (-not (Test-Path "venv")) {
    Write-Host "Creando entorno virtual..."
    python -m venv venv
}
else {
    Write-Host "El entorno virtual ya existe."
}

Write-Host "Instalando dependencias..."
& ".\venv\Scripts\python.exe" -m pip install -r requirements-pruebas.txt

if (-not (Test-Path "repo")) {
    Write-Host "Clonando repositorio del Grupo 6..."
    git clone $repoUrl repo
}
else {
    Write-Host "El repositorio del Grupo 6 ya existe."
}

Write-Host "Fijando version evaluada..."
git -C repo checkout $commitGrupo6

Write-Host ""
Write-Host "=== Entorno listo ==="
Write-Host "Version evaluada del Grupo 6: $commitGrupo6"
