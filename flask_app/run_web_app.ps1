# Flask Web Application Startup Script
# Run this script to start the Startup Deal Evaluator web application

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Write-Host "Starting Startup Deal Evaluator Web Application" -ForegroundColor Cyan
# Use PadLeft for compatibility with Windows PowerShell 5.1 (string multiplication isn't supported)
$line = ''.PadLeft(50,'=')
Write-Host $line -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed. Please install Python 3.8+ first." -ForegroundColor Red
    Write-Host "   Download from: https://python.org/downloads" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Navigate to Flask app directory (this script lives in the app folder)
$flaskDir = $PSScriptRoot
if (Test-Path $flaskDir) {
    Set-Location $flaskDir
    Write-Host "Changed to Flask app directory: $flaskDir" -ForegroundColor Green
} else {
    Write-Host "Flask app directory not found: $flaskDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Fast-start defaults (can be overridden by environment)
# Enable Kaggle by default; script will gracefully fall back to local cached CSV if needed
if (-not $env:SKIP_KAGGLE) { $env:SKIP_KAGGLE = 'false' }
if (-not $env:PRECOMPUTE_MAX_ROWS) { $env:PRECOMPUTE_MAX_ROWS = '200' }

# Resolve Python command (prefer 'python', fallback to 'py -3')
$pythonCmd = 'python'
try {
    $null = & $pythonCmd --version 2>$null
}
catch {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $pythonCmd = 'py -3'
        Write-Host "INFO: Using Python via launcher: $pythonCmd" -ForegroundColor Yellow
    }
}

# Load Kaggle credentials from local file if present and env vars not set
try {
    if (-not $env:KAGGLE_USERNAME -or -not $env:KAGGLE_KEY) {
        $kaggleFile = Join-Path $flaskDir 'kaggle.json'
        if (Test-Path $kaggleFile) {
            $kcreds = Get-Content $kaggleFile | ConvertFrom-Json
            if (-not $env:KAGGLE_USERNAME -and $kcreds.username) { $env:KAGGLE_USERNAME = $kcreds.username }
            if (-not $env:KAGGLE_KEY -and $kcreds.key) { $env:KAGGLE_KEY = $kcreds.key }
            Write-Host "Kaggle credentials loaded from kaggle.json" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "WARNING: Could not load Kaggle credentials from kaggle.json: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Determine whether to use venv (default yes, but can be disabled)
$useVenv = $true
if ($env:USE_VENV) {
    $useVenv = -not ($env:USE_VENV.ToLower() -in @('0','false','no','off'))
}

# Check if virtual environment exists (only if using venv)
$venvPython = $null
if ($useVenv) {
    $venvPath = "venv"
    if (!(Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        & $pythonCmd -m venv venv
    Write-Host "Virtual environment created" -ForegroundColor Green
    }

    # Ensure venv python is available
    $venvPython = Join-Path $flaskDir "venv\Scripts\python.exe"
    if (!(Test-Path $venvPython)) {
    Write-Host "venv Python not found at $venvPython; will fall back to system Python" -ForegroundColor Yellow
        $useVenv = $false
    }
}

# Install/upgrade dependencies (venv preferred, fallback to user site if needed)
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
$usingVenv = $useVenv
if ($useVenv) {
    try {
        & $venvPython -m pip install --upgrade pip
        & $venvPython -m pip install -r requirements.txt
    Write-Host "Dependencies installed (venv)" -ForegroundColor Green
    } catch {
    # Print the resolved venv python path without escaping (show value, not literal)
    Write-Host "WARNING: Failed to install with venv Python ($venvPython). Falling back to user site-packages..." -ForegroundColor Yellow
        $usingVenv = $false
        & $pythonCmd -m pip install --user --upgrade pip
        & $pythonCmd -m pip install --user -r requirements.txt
    Write-Host "Dependencies installed (user site)" -ForegroundColor Green
    }
} else {
    & $pythonCmd -m pip install --user --upgrade pip
    & $pythonCmd -m pip install --user -r requirements.txt
    Write-Host "Dependencies installed (user site)" -ForegroundColor Green
}

# Set environment variables
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

Write-Host ""
Write-Host "Flask Web Application Configuration:" -ForegroundColor Cyan
Write-Host "   ML Models: Training on startup..." -ForegroundColor White
Write-Host "   Web Server: http://localhost:5000" -ForegroundColor White
Write-Host "   API Endpoints: /api/evaluate, /api/examples" -ForegroundColor White
Write-Host "   Debug Mode: Enabled" -ForegroundColor White
Write-Host ""

Write-Host "Starting Flask development server..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Flask application
try {
    if ($usingVenv -and $venvPython) {
        & $venvPython app.py
    } else {
        & $pythonCmd app.py
    }
} catch {
    Write-Host "Error starting Flask application:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Flask application stopped" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}