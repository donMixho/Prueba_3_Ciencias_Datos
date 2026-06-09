@echo off
REM ============================================================
REM   Inicia el Dashboard (Streamlit) del proyecto NHANES.
REM   Haz DOBLE CLIC en este archivo para verlo en el navegador.
REM   Se abrira en: http://localhost:8501
REM   Para detenerlo: cierra esta ventana negra.
REM ============================================================
cd /d "%~dp0"
set REPORTING_DIR=data\08_reporting
set API_URL=http://localhost:8000
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo.
echo  Iniciando el dashboard... espera unos segundos.
echo  Se abrira solo en tu navegador (http://localhost:8501)
echo  NO cierres esta ventana mientras lo uses.
echo.

python -m streamlit run dashboards\app.py --server.port 8501

echo.
echo  El dashboard se detuvo. Puedes cerrar esta ventana.
pause
