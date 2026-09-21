@echo off
setlocal
title AB-GEN Research Demo
color 0A

echo.
echo  =============================================================
echo   AB-GEN Research Demo - Recovered Cached-PCA Diagnostics
echo   Evidence-first diagnostic path; not a clean RAW baseline
 echo  =============================================================
echo.

:: Runtime contract: explicit read-only-style artifact directory + manifest.
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

:: Step 3: Install demo dependencies
 echo  [2/3] Installing demo dependencies...
python -m pip install -q -r requirements_demo.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause & exit /b 1
)

:: Step 4: Launch. app.py performs manifest/hash preflight before deserialization.
echo.
echo  [3/3] Launching AB-GEN diagnostic demo...
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
echo  [ERROR] Required runtime artifacts are missing from .\artifacts\
echo.
echo  Required files:
echo    - artifacts\abgen_bundle.pkl
echo    - artifacts\sample_data.pkl
echo    - artifacts\training_module.py
echo    - artifacts\runtime-manifest.json
echo.
echo  Do not search parent folders or load arbitrary serialized artifacts.
echo  See artifacts\README.md, SECURITY.md and REPRODUCIBILITY.md.
echo.
pause
exit /b 2

:missing_manifest
echo  [ERROR] artifacts\runtime-manifest.json is missing.
echo  Startup is intentionally blocked before model deserialization.
echo  Use a manifest from the trusted AB-GEN evidence/release package.
echo.
pause
exit /b 3
