@echo off
chcp 65001 >nul
title ollacode - Asistente AI

:: Obtener ruta donde está este batch
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "VENV_DIR=%SCRIPT_DIR%.venv_windows"

:: Detectar Python
set "PYTHON="
where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=py -3"
    goto :found
)
where python >nul 2>nul
if %errorlevel% equ 0 (
    python --version 2>nul | find "3." >nul
    if %errorlevel% equ 0 set "PYTHON=python"
)
if not defined PYTHON (
    echo ========================================
    echo  ollacode - Asistente AI
    echo ========================================
    echo.
    echo  ERROR: Python 3 no encontrado
    echo.
    echo  Instala Python 3 desde:
    echo  https://www.python.org/downloads/
    echo.
    echo  Marca "Add Python to PATH" al instalarlo
    echo.
    pause
    exit /b 1
)

:found
echo ========================================
echo  ollacode - Asistente AI
echo ========================================
echo.

:: Crear/actualizar venv si no existe
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [1/3] Creando entorno virtual...
    %PYTHON% -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo Error creando entorno virtual
        pause
        exit /b 1
    )
)

:: Activar venv
call "%VENV_DIR%\Scripts\activate.bat"

:: Instalar dependencias
echo [2/3] Instalando dependencias...
python -m pip install --upgrade pip -q
python -m pip install rich httpx PyMuPDF psutil -q
:: duckduckgo-search es opcional para web_search
python -m pip install duckduckgo-search -q 2>nul

:: Lanzar ollacode
echo [3/3] Iniciando ollacode...
echo.
python -m ollacode.__main__ %*

:: Si falló, mostrar error
if %errorlevel% neq 0 (
    echo.
    echo Error al ejecutar ollacode (codigo: %errorlevel%)
    pause
)

deactivate
