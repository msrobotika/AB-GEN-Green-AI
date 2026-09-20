@echo off
title AB-GEN Research Demo
color 0A

echo.
echo  =============================================================
echo   AB-GEN Research Demo - CIFAR-10 Cached-PCA Inference
echo   Geometric + Spectral + Polynomial Ensemble
echo  =============================================================
echo.

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

:: Step 3: Install dependencies
echo  [2/3] Installing demo dependencies...
python -m pip install -q -r requirements_demo.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause & exit /b 1
)

:: Step 4: Launch server
echo.
echo  [3/3] Launching AB-GEN Research Demo...
echo  Open your browser at: http://localhost:5000
echo  Press Ctrl+C to stop the server.
echo.
python app.py
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] The demo server exited with an error.
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
echo  Do NOT try to generate them from an assumed parent folder.
echo  Use only artifacts produced by the validated AB-GEN release process.
echo  See README.md and REPRODUCIBILITY.md for the current evidence status.
echo.
pause
exit /b 2
