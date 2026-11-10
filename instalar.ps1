# ChartForge — instalador (una sola vez)
# Escribe la venv, los paquetes y los modelos TODO dentro de D:\charf1\,
# para que desinstalar sea borrar la carpeta.
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $raiz

Write-Host "=== ChartForge instalacion (1/6): ffmpeg ==="
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Host "ERROR: no se encontro ffmpeg en el PATH."
    Write-Host "Descargalo de https://www.gyan.dev/ffmpeg/builds/ o 'winget install Gyan.FFmpeg',"
    Write-Host "agregalo al PATH y vuelve a correr este script."
    exit 1
}
Write-Host ("ffmpeg OK: " + $ffmpeg.Source)

Write-Host "=== (2/6): espacio libre en el disco del proyecto ==="
$unidad = (Resolve-Path $raiz).Drive.Name   # la unidad REAL donde vive el proyecto
python -c "import sys,chartforge.descarga_modelos as dm; ok,msg=dm.hay_espacio(sys.argv[1]); print(msg)" "$unidad\"
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: no hay espacio suficiente en $unidad."; exit 1 }

Write-Host "=== (3/6): entorno virtual venv\ ==="
if (-not (Test-Path "$raiz\venv")) {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR creando la venv."; exit 1 }
} else {
    Write-Host "venv ya existia; se reutiliza."}
$py = Join-Path $raiz "venv\Scripts\python.exe"
& $py --version

$env:PIP_CACHE_DIR = Join-Path $raiz ".pipcache"

Write-Host "=== (4/6): torch solo-CPU (evita bajar CUDA de ~2.5 GB) ==="
& $py -m pip install --index-url https://download.pytorch.org/whl/cpu torch
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR instalando torch."; exit 1 }

Write-Host "=== (5/6): resto del requirements.txt ==="
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR instalando paquetes."; exit 1 }

Write-Host "=== (6/6): descarga de modelos dentro de modelos\ ==="
$env:TORCH_HOME = Join-Path $raiz "modelos\torch"
$env:HF_HOME = Join-Path $raiz "modelos\hf"
& $py -m chartforge.descarga_modelos --todo
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR descargando modelos."; exit 1 }

# convertir.bat en la raiz del proyecto: arrastrar un MP3/FLAC sobre el
$bat = @"
@echo off
rem ChartForge - convierte una cancion: arrastra un archivo MP3 o FLAC sobre este
set RAIZ=%~dp0
if not exist "%RAIZ%venv\Scripts\python.exe" (
    echo.
    echo ERROR: falta la instalacion de ChartForge ^(no hay venv^).
    echo Corre primero: powershell -ExecutionPolicy Bypass -File "%RAIZ%instalar.ps1"
    pause
    exit /b 1
)
pushd "%RAIZ%"
"%RAIZ%venv\Scripts\python.exe" -m chartforge.cli %*
set COD=%ERRORLEVEL%
if not "%COD%"=="0" (
    echo.
    echo La conversion termino con error.
    pause
)
popd
"@
Set-Content -Path (Join-Path $raiz "convertir.bat") -Value $bat -Encoding Ascii
Write-Host "convertir.bat creado en $raiz"

function TamanoMB([string]$ruta) {
    if (-not (Test-Path $ruta)) { return 0 }
    $sum = (Get-ChildItem -Recurse -Force $ruta -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    return [math]::Round($sum / 1MB, 1)
}

Write-Host ("Tamanos finales: venv = " + (TamanoMB "$raiz\venv") + " MB; modelos = " + (TamanoMB "$raiz\modelos") + " MB; cache pip = " + (TamanoMB "$raiz\.pipcache") + " MB")
Write-Host "Instalacion completa. Para convertir una cancion, arrastra un MP3/FLAC sobre convertir.bat."
