@echo off
title Iniciar Sistema CAMBRI

echo ============================================
echo      INICIANDO SISTEMA CAMBRI
echo ============================================
echo.

:: Verificar si existe el entorno virtual
if not exist "venv" (
    echo [1/4] Creando entorno virtual...
    python -m venv venv

    echo.
    echo [2/4] Activando entorno virtual...
    call venv\Scripts\activate

    echo.
    echo [3/4] Instalando dependencias...
    pip install -r requirements.txt
) else (
    echo [OK] Entorno virtual ya existe.
    
    echo.
    echo [2/4] Activando entorno virtual...
    call venv\Scripts\activate
)

echo.
echo [4/4] Ejecutando sistema...
python run.py

echo.
echo El sistema se ha detenido.
pause