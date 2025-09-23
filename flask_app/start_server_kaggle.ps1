# Kaggle-enabled launcher: set env and run Flask app without venv
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
Set-Location $PSScriptRoot
$env:SKIP_KAGGLE = 'false'
$env:PRECOMPUTE_MAX_ROWS = '200'
$env:FLASK_ENV = 'development'
# Load Kaggle credentials if available
try {
	if (-not $env:KAGGLE_USERNAME -or -not $env:KAGGLE_KEY) {
		$kaggleFile = Join-Path $PSScriptRoot 'kaggle.json'
		if (Test-Path $kaggleFile) {
			$kcreds = Get-Content $kaggleFile | ConvertFrom-Json
			if (-not $env:KAGGLE_USERNAME -and $kcreds.username) { $env:KAGGLE_USERNAME = $kcreds.username }
			if (-not $env:KAGGLE_KEY -and $kcreds.key) { $env:KAGGLE_KEY = $kcreds.key }
			Write-Host "🔐 Kaggle credentials loaded from kaggle.json" -ForegroundColor Green
		}
	}
} catch {}
Write-Host "Starting Deal Scout with Kaggle enabled on http://127.0.0.1:5000" -ForegroundColor Cyan
python app.py
