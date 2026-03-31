@echo off
title AB-GEN 80%% Accuracy - M5 Green AI Demo
color 0A

echo.
echo  =============================================================
echo   AB-GEN 80%% Accuracy - CIFAR-10 Live Inference Demo
echo   M5 Green AI -- Geometric + Polynomial Ensemble
echo  =============================================================
echo.

:: ── Step 1: Check Python ─────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python 3.10 or later.
    pause & exit /b 1
)

:: ── Step 2: Install dependencies ─────────────────────────
echo  [1/3] Installing dependencies...
pip install -q -r requirements_demo.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause & exit /b 1
)

:: ── Step 3: Generate bundles if needed ───────────────────
if not exist "abgen_bundle.pkl" (
    echo.
    echo  [2/3] Bundle not found. Generating from parent project...
    cd ..
    python AB-GEN_GITHUB_DEMO\export_bundle.py
    cd AB-GEN_GITHUB_DEMO
) else (
    echo  [2/3] Bundle already found. Skipping export.
)

:: ── Step 4: Launch server ────────────────────────────────
echo.
echo  [3/3] Launching AB-GEN Demo Dashboard...
echo  Open your browser at: http://localhost:5000
echo  Press Ctrl+C to stop the server.
echo.
python app.py

pause
