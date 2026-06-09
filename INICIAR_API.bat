@echo off
REM ============================================================
REM   Inicia la API REST (FastAPI) del proyecto NHANES.
REM   Haz DOBLE CLIC en este archivo para iniciarla.
REM   Documentacion interactiva en: http://localhost:8000/docs
REM   Para detenerla: cierra esta ventana negra.
REM ============================================================
cd /d "%~dp0"
set REPORTING_DIR=data\08_reporting

echo.
echo  Iniciando la API... espera unos segundos.
echo  Abre en el navegador: http://localhost:8000/docs
echo  NO cierres esta ventana mientras la uses.
echo.

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

echo.
echo  La API se detuvo. Puedes cerrar esta ventana.
pause
