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
