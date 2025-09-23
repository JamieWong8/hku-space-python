@echo off
setlocal
echo Starting Flask Application...

REM Change to this script's directory
cd /d "%~dp0"

REM Use venv's python if available
set "VENV_PY=%~dp0venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
	echo Virtual environment not found. Creating one...
	py -3 -m venv venv
)

if exist "%VENV_PY%" (
	echo Installing/Updating dependencies...
	"%VENV_PY%" -m pip install --upgrade pip >nul 2>&1
	"%VENV_PY%" -m pip install -r requirements.txt >nul 2>&1
	echo Launching app with venv Python...
	"%VENV_PY%" app.py
) else (
	echo venv python not found. Falling back to system Python...
	python app.py
)

pause
endlocal