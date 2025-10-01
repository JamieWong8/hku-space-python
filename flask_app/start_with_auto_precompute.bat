@echo off
REM Start Deal Scout Web Application with Auto-Precompute
REM This script ensures precomputation happens automatically

echo ============================================================
echo Deal Scout - Starting Web Application
echo ============================================================
echo.

cd /d "%~dp0"

REM Set environment variables for optimal startup
set AUTO_TRAIN_ON_IMPORT=false
set BOOTSTRAP_FAST=true
set LAZY_BACKGROUND_TRAIN=true
set PRECOMPUTE_DISABLE=false

echo Configuration:
echo   - Fast Bootstrap: Enabled (300 sample companies)
echo   - Background Training: Enabled (full dataset)
echo   - Auto-Precompute: Enabled (after training)
echo.
echo Starting Flask server...
echo Web interface will be available at: http://localhost:5000
echo.
echo NOTE: Precomputation will run automatically in the background.
echo       It may take 2-5 minutes to complete.
echo.

REM Start the Flask app
"%~dp0..\.venv\Scripts\python.exe" "%~dp0app.py"

pause
