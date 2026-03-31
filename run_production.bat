@echo off
title AB-GEN 80%% Accuracy - PRODUCTION Server
color 0A

echo.
echo  =============================================================
echo   AB-GEN 80%% Accuracy - Production Deployment (Waitress)
echo   M5 Green AI -- Geometric + Polynomial Ensemble
echo  =============================================================
echo.

:: ── Optional: set host / port / threads via environment ──────────────
:: Uncomment to override defaults:
:: set ABGEN_HOST=0.0.0.0
:: set ABGEN_PORT=5000
:: set ABGEN_THREADS=4

:: ── Install production dependencies ──────────────────────────────────
echo  [1/2] Installing production dependencies (waitress + ML stack)...
pip install -q -r requirements_prod.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause & exit /b 1
)

:: ── Launch production server ──────────────────────────────────────────
echo.
echo  [2/2] Launching AB-GEN Production Server (Waitress WSGI)...
echo  Open your browser at: http://localhost:5000
echo  Press Ctrl+C to stop.
echo.
python serve.py

pause
