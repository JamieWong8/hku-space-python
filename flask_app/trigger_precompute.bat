@echo off
REM Trigger Precomputation for Deal Scout
REM Run this after starting the Flask server

echo ============================================================
echo Deal Scout - Trigger Precomputation
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not found in PATH
    echo Please ensure Python is installed and in your PATH
    pause
    exit /b 1
)

REM Run the Python script
python trigger_precompute.py

echo.
pause
