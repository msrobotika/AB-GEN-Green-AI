@echo off
setlocal
cd /d "%~dp0"
title AB-GEN Research Demo - Production Server
color 0A

echo.
echo  =============================================================
echo   AB-GEN Research Demo - Production Diagnostic Deployment
echo   Waitress + trusted artifact manifest preflight
echo  =============================================================
echo.

:: Optional host / port / threads overrides may be set before calling this file.
if not defined ABGEN_HOST set "ABGEN_HOST=0.0.0.0"
if not defined ABGEN_PORT set "ABGEN_PORT=5000"
if not defined ABGEN_THREADS set "ABGEN_THREADS=4"

set "ABGEN_BUNDLE_PATH=%CD%\artifacts\abgen_bundle.pkl"
set "ABGEN_SAMPLE_DATA_PATH=%CD%\artifacts\sample_data.pkl"
set "ABGEN_TRAINING_MODULE_PATH=%CD%\artifacts\training_module.py"
set "ABGEN_ARTIFACT_MANIFEST_PATH=%CD%\artifacts\runtime-manifest.json"
set "ABGEN_REQUIRE_MANIFEST=1"

:: Step 1: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Install the supported Python version documented by the accepted environment.
    pause & exit /b 1
)

:: Step 2: Require the complete trusted runtime set
if not exist "%ABGEN_BUNDLE_PATH%" goto :missing_artifacts
if not exist "%ABGEN_SAMPLE_DATA_PATH%" goto :missing_artifacts
if not exist "%ABGEN_TRAINING_MODULE_PATH%" goto :missing_artifacts
if not exist "%ABGEN_ARTIFACT_MANIFEST_PATH%" goto :missing_manifest

echo  [1/3] Runtime artifact set and manifest found.

:: Step 3: Install the explicit production dependency contract
echo  [2/3] Installing production dependencies...
python -m pip install -q -r requirements_prod.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install production dependencies.
    pause & exit /b 1
)

:: Step 4: serve.py verifies hashes before deserialization and requires Waitress.
echo.
echo  [3/3] Launching AB-GEN production diagnostic server...
echo  Open your browser at: http://%ABGEN_HOST%:%ABGEN_PORT%
echo  Press Ctrl+C to stop.
echo.
python serve.py
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Production startup or server execution failed.
    pause & exit /b 1
)

goto :eof

:missing_artifacts
echo  [ERROR] Required runtime artifacts are missing from .\artifacts\
echo.
echo  Required files:
echo    - artifacts\abgen_bundle.pkl
echo    - artifacts\sample_data.pkl
echo    - artifacts\training_module.py
echo    - artifacts\runtime-manifest.json
echo.
echo  Use only trusted artifacts from the accepted AB-GEN evidence/release package.
echo  See artifacts\README.md, SECURITY.md and REPRODUCIBILITY.md.
echo.
pause
exit /b 2

:missing_manifest
echo  [ERROR] artifacts\runtime-manifest.json is missing.
echo  Production startup is intentionally blocked before deserialization.
echo.
pause
exit /b 3
