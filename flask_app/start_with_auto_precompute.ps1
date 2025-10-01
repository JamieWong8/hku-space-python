# Start Deal Scout Web Application with Auto-Precompute
# This script ensures precomputation happens automatically

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Deal Scout - Starting Web Application" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Set environment variables for optimal startup
$env:AUTO_TRAIN_ON_IMPORT = 'false'
$env:BOOTSTRAP_FAST = 'true'
$env:LAZY_BACKGROUND_TRAIN = 'true'
$env:PRECOMPUTE_DISABLE = 'false'

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  - Fast Bootstrap: Enabled (300 sample companies)" -ForegroundColor Gray
Write-Host "  - Background Training: Enabled (full dataset)" -ForegroundColor Gray
Write-Host "  - Auto-Precompute: Enabled (after training)" -ForegroundColor Green
Write-Host ""

Write-Host "Starting Flask server..." -ForegroundColor Yellow
Write-Host "Web interface will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""

Write-Host "NOTE: Precomputation will run automatically in the background." -ForegroundColor Yellow
Write-Host "      It may take 2-5 minutes to complete." -ForegroundColor Yellow
Write-Host "      Watch for the message: '✅ Auto-precompute completed'" -ForegroundColor Gray
Write-Host ""

# Start the Flask app
$pythonPath = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$appPath = Join-Path $PSScriptRoot "app.py"

& $pythonPath $appPath
