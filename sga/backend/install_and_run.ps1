#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script de instalación y arranque del backend SGA.
    
.DESCRIPTION
    Crea un entorno virtual Python, instala las dependencias del proyecto
    y ofrece opciones para levantar el servidor o ejecutar las pruebas.

.USAGE
    cd sga\backend
    .\install_and_run.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SGA Backend – Instalador y Runner" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Find Python ────────────────────────────────────────────────────────────
$pythonCandidates = @(
    "python",
    "python3",
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe",
    "C:\Python39\python.exe",
    "C:\Program Files\Python313\python.exe",
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python310\python.exe"
)

$PYTHON = $null
foreach ($candidate in $pythonCandidates) {
    try {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python 3\.\d+") {
            $PYTHON = $candidate
            Write-Host "[OK] Python encontrado: $PYTHON ($ver)" -ForegroundColor Green
            break
        }
    } catch { }
}

if (-not $PYTHON) {
    Write-Host "[ERROR] Python 3 no encontrado en el sistema." -ForegroundColor Red
    Write-Host "Instala Python 3.10+ desde https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Asegúrate de marcar 'Add Python to PATH' durante la instalación." -ForegroundColor Yellow
    exit 1
}

# ── 2. Create / activate virtual environment ──────────────────────────────────
$venvDir = ".\venv"
if (-not (Test-Path $venvDir)) {
    Write-Host ""
    Write-Host "[INFO] Creando entorno virtual en $venvDir ..." -ForegroundColor Yellow
    & $PYTHON -m venv $venvDir
}

$activateScript = "$venvDir\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "[ERROR] No se pudo crear el entorno virtual." -ForegroundColor Red
    exit 1
}

. $activateScript
Write-Host "[OK] Entorno virtual activado." -ForegroundColor Green

# ── 3. Upgrade pip and install dependencies ───────────────────────────────────
Write-Host ""
Write-Host "[INFO] Instalando dependencias..." -ForegroundColor Yellow
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -e . --quiet   # installs backend as editable package

Write-Host "[OK] Dependencias instaladas correctamente." -ForegroundColor Green

# ── 4. Ask user what to do ────────────────────────────────────────────────────
Write-Host ""
Write-Host "¿Qué deseas hacer?" -ForegroundColor Cyan
Write-Host "  [1] Ejecutar el servidor de desarrollo (uvicorn)"
Write-Host "  [2] Correr las pruebas (pytest)"
Write-Host "  [3] Ambas (tests primero, luego servidor)"
Write-Host ""
$choice = Read-Host "Selección"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "[INFO] Iniciando servidor en http://localhost:8000 ..." -ForegroundColor Cyan
        Write-Host "       Documentación en http://localhost:8000/docs" -ForegroundColor Gray
        Write-Host ""
        $env:DATABASE_URL = "sqlite:///./sga_dev.db"
        uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
    }
    "2" {
        Write-Host ""
        Write-Host "[INFO] Ejecutando pruebas..." -ForegroundColor Cyan
        pytest tests/ -v --tb=short
    }
    "3" {
        Write-Host ""
        Write-Host "[INFO] Ejecutando pruebas..." -ForegroundColor Cyan
        pytest tests/ -v --tb=short
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[INFO] Pruebas exitosas. Iniciando servidor..." -ForegroundColor Green
            $env:DATABASE_URL = "sqlite:///./sga_dev.db"
            uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
        } else {
            Write-Host "[ERROR] Las pruebas fallaron. Revisa los errores antes de iniciar el servidor." -ForegroundColor Red
            exit 1
        }
    }
    default {
        Write-Host "Opción no válida. Ejecuta el script nuevamente." -ForegroundColor Yellow
    }
}
