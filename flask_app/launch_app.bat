@echo off
setlocal
echo Starting Deal Scout (no-venv) ...

REM Change to this script's directory
cd /d "%~dp0"

REM Fast-start environment variables
set SKIP_KAGGLE=false
set PRECOMPUTE_MAX_ROWS=50
set FLASK_ENV=development

echo Using Python: %PYTHON%
echo Working dir: %CD%
echo Starting server on http://127.0.0.1:5000 ...

python app.py

endlocal
