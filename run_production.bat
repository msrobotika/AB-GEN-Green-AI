@echo off
title AB-GEN Research Demo - Production Server
color 0A

echo.
echo  =============================================================
echo   AB-GEN Research Demo - Production Deployment (Waitress)
echo   Geometric + Spectral + Polynomial Ensemble
echo  =============================================================
echo.

:: Optional host / port / threads overrides:
:: set ABGEN_HOST=0.0.0.0
:: set ABGEN_PORT=5000
:: set ABGEN_THREADS=4

:: Step 1: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python 3.11.
    pause & exit /b 1
)

:: Step 2: Validate required runtime artifacts
if not exist "abgen_bundle.pkl" goto :missing_artifacts
if not exist "sample_data.pkl" goto :missing_artifacts

echo  [1/3] Runtime artifacts found.

:: Step 3: Install production dependencies
echo  [2/3] Installing production dependencies...
python -m pip install -q -r requirements_prod.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause & exit /b 1
)

:: Step 4: Launch production server
echo.
echo  [3/3] Launching AB-GEN production server...
echo  Open your browser at: http://localhost:5000
echo  Press Ctrl+C to stop.
echo.
python serve.py
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] The production server exited with an error.
    pause & exit /b 1
)

goto :eof

:missing_artifacts
echo  [ERROR] Required runtime artifacts are missing.
echo.
echo  This public repository is not yet a standalone reproducible package.
echo  Required files:
echo    - abgen_bundle.pkl
echo    - sample_data.pkl
echo.
echo  Use only artifacts produced by the validated AB-GEN release process.
echo  See README.md and REPRODUCIBILITY.md for the current evidence status.
echo.
pause
exit /b 2
