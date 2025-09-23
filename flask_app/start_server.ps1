# Simple launcher: set env and run Flask app without venv
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
Set-Location -LiteralPath $PSScriptRoot

# Default environment
$env:SKIP_KAGGLE = 'false'
$env:PRECOMPUTE_MAX_ROWS = '50'
$env:FLASK_ENV = 'development'

# Load Kaggle credentials from local file if not already set
$kaggleFile = Join-Path $PSScriptRoot 'kaggle.json'
if ([string]::IsNullOrEmpty($env:KAGGLE_USERNAME) -or [string]::IsNullOrEmpty($env:KAGGLE_KEY)) {
	if (Test-Path -LiteralPath $kaggleFile) {
		try {
			$kcreds = Get-Content -LiteralPath $kaggleFile -Raw | ConvertFrom-Json
			if ($kcreds.username) { $env:KAGGLE_USERNAME = $kcreds.username }
			if ($kcreds.key) { $env:KAGGLE_KEY = $kcreds.key }
			Write-Host "Kaggle credentials loaded from kaggle.json"
		} catch {
			Write-Host "Warning: Could not load kaggle.json: $($_.Exception.Message)"
		}
	}
}

Write-Host "Starting Deal Scout on http://127.0.0.1:5000 (development)"
python app.py
