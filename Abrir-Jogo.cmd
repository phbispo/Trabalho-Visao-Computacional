@echo off
setlocal
cd /d "%~dp0" || exit /b 1
set "PYTHONPATH="
set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    where py >nul 2>&1
    if errorlevel 1 (
        python -m venv .venv
    ) else (
        py -3 -m venv .venv
    )
    if errorlevel 1 goto falha
)

"%PYTHON%" -c "import cv2; from PIL import Image; from mediapipe.tasks.python import BaseOptions, vision" >nul 2>&1
if errorlevel 1 (
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto falha
)

"%PYTHON%" quebra_cabeca.py %*
if errorlevel 1 goto falha
exit /b 0

:falha
echo Falha ao iniciar. Confira a mensagem acima.
pause
exit /b 1
