# Flask App Cleanup Script
# Removes unnecessary files and duplicate virtual environments
# Run this from the flask_app directory

Write-Host "🧹 Flask App Cleanup Script" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""

$flaskAppPath = "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
cd $flaskAppPath

# Calculate initial size
Write-Host "📊 Calculating initial size..." -ForegroundColor Yellow
$initialSize = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "📊 Initial size: $([math]::Round($initialSize, 2)) MB" -ForegroundColor Yellow
Write-Host ""

# Track deleted items
$deletedItems = @()
$totalSaved = 0

# 1. Delete duplicate venv/ (keeping .venv/)
if (Test-Path "venv") {
    Write-Host "🔍 Found: venv/ directory" -ForegroundColor White
    $venvSize = (Get-ChildItem "venv" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   Size: $([math]::Round($venvSize, 2)) MB" -ForegroundColor Gray
    Write-Host "   Status: DUPLICATE (will keep .venv/ instead)" -ForegroundColor Yellow
    Write-Host "🗑️  Deleting venv/..." -ForegroundColor Red
    
    try {
        Remove-Item -Path "venv" -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Deleted venv/" -ForegroundColor Green
        $venvSizeStr = [math]::Round($venvSize, 2).ToString() + " MB"
        $deletedItems += "venv/ ($venvSizeStr)"
        $totalSaved += $venvSize
    } catch {
        Write-Host "Error deleting venv/: $_" -ForegroundColor Red
    }
    Write-Host ""
} else {
    Write-Host "ℹ️  venv/ not found (already clean)" -ForegroundColor Gray
    Write-Host ""
}

# 2. Delete .model_cache/
if (Test-Path ".model_cache") {
    Write-Host "🔍 Found: .model_cache/ directory" -ForegroundColor White
    $cacheSize = (Get-ChildItem ".model_cache" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   Size: $([math]::Round($cacheSize, 2)) MB" -ForegroundColor Gray
    Write-Host "   Status: Will regenerate on next startup" -ForegroundColor Yellow
    Write-Host "🗑️  Deleting .model_cache/..." -ForegroundColor Red
    
    try {
        Remove-Item -Path ".model_cache" -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Deleted .model_cache/" -ForegroundColor Green
        $cacheSizeStr = [math]::Round($cacheSize, 2).ToString() + " MB"
        $deletedItems += ".model_cache/ ($cacheSizeStr)"
        $totalSaved += $cacheSize
    } catch {
        Write-Host "Error deleting .model_cache/: $_" -ForegroundColor Red
    }
    Write-Host ""
} else {
    Write-Host "ℹ️  .model_cache/ not found" -ForegroundColor Gray
    Write-Host ""
}

# 3. Delete __pycache__/
if (Test-Path "__pycache__") {
    Write-Host "🔍 Found: __pycache/ directory" -ForegroundColor White
    $pycacheSize = (Get-ChildItem "__pycache__" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   Size: $([math]::Round($pycacheSize, 2)) MB" -ForegroundColor Gray
    Write-Host "   Status: Python bytecode cache (auto-regenerates)" -ForegroundColor Yellow
    Write-Host "🗑️  Deleting __pycache__/..." -ForegroundColor Red
    
    try {
        Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Deleted __pycache__/" -ForegroundColor Green
        $pycacheSizeStr = [math]::Round($pycacheSize, 2).ToString() + " MB"
        $deletedItems += "__pycache__/ ($pycacheSizeStr)"
        $totalSaved += $pycacheSize
    } catch {
        Write-Host "Error deleting __pycache__/: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Also delete nested __pycache__ directories
Write-Host "🔍 Searching for nested __pycache__ directories..." -ForegroundColor White
$nestedPycache = Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue
if ($nestedPycache) {
    foreach ($dir in $nestedPycache) {
        Write-Host "🗑️  Deleting $($dir.FullName)..." -ForegroundColor Red
        try {
            Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction Stop
            Write-Host "Deleted $($dir.Name)" -ForegroundColor Green
        } catch {
            Write-Host "Error deleting $($dir.Name): $_" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# 4. Delete .pytest_cache/
if (Test-Path ".pytest_cache") {
    Write-Host "🔍 Found: .pytest_cache/ directory" -ForegroundColor White
    Write-Host "   Status: Test cache (auto-regenerates)" -ForegroundColor Yellow
    Write-Host "🗑️  Deleting .pytest_cache/..." -ForegroundColor Red
    
    try {
        Remove-Item -Path ".pytest_cache" -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Deleted .pytest_cache/" -ForegroundColor Green
        $deletedItems += ".pytest_cache/"
    } catch {
        Write-Host "Error deleting .pytest_cache/: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# 5. Delete debug_log.txt
if (Test-Path "debug_log.txt") {
    Write-Host "🔍 Found: debug_log.txt" -ForegroundColor White
    Write-Host "   Status: Old debug logs" -ForegroundColor Yellow
    Write-Host "🗑️  Deleting debug_log.txt..." -ForegroundColor Red
    
    try {
        Remove-Item -Path "debug_log.txt" -Force -ErrorAction Stop
        Write-Host "✅ Deleted debug_log.txt" -ForegroundColor Green
        $deletedItems += "debug_log.txt"
    } catch {
        Write-Host "Error deleting debug_log.txt: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Optional: Delete kaggle_data/ (commented out by default)
# Uncomment to delete kaggle_data/ directory
<#
if (Test-Path "kaggle_data") {
    Write-Host "🔍 Found: kaggle_data/ directory" -ForegroundColor White
    $kaggleSize = (Get-ChildItem "kaggle_data" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   Size: $([math]::Round($kaggleSize, 2)) MB" -ForegroundColor Gray
    Write-Host "   Status: Will re-download from Kaggle if needed" -ForegroundColor Yellow
    Write-Host "🗑️  Deleting kaggle_data/..." -ForegroundColor Red
    
    try {
        Remove-Item -Path "kaggle_data" -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Deleted kaggle_data/" -ForegroundColor Green
        $kaggleSizeStr = [math]::Round($kaggleSize, 2).ToString() + " MB"
        $deletedItems += "kaggle_data/ ($kaggleSizeStr)"
        $totalSaved += $kaggleSize
    } catch {
        Write-Host "Error deleting kaggle_data/: $_" -ForegroundColor Red
    }
    Write-Host ""
}
#>

# Summary
Write-Host "═══════════════════════════════════" -ForegroundColor Cyan
Write-Host "🎉 Cleanup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($deletedItems.Count -gt 0) {
    Write-Host "🗑️  Deleted Items:" -ForegroundColor Yellow
    foreach ($item in $deletedItems) {
        Write-Host "   • $item" -ForegroundColor White
    }
    Write-Host ""
}

# Calculate final size
Write-Host "📊 Calculating final size..." -ForegroundColor Yellow
$finalSize = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
$saved = $initialSize - $finalSize

Write-Host "📊 Initial size:  $([math]::Round($initialSize, 2)) MB" -ForegroundColor White
Write-Host "📊 Final size:    $([math]::Round($finalSize, 2)) MB" -ForegroundColor White
$percentSaved = [math]::Round(($saved/$initialSize)*100, 1)
Write-Host "💾 Space saved:   $([math]::Round($saved, 2)) MB ($percentSaved percent)" -ForegroundColor Cyan
Write-Host ""

# Verification
Write-Host "Verification:" -ForegroundColor Green
if (Test-Path ".venv") {
    Write-Host "   .venv/ directory: EXISTS" -ForegroundColor Green
} else {
    Write-Host "   .venv/ directory: MISSING (WARNING!)" -ForegroundColor Red
}

if (Test-Path "app.py") {
    Write-Host "   app.py: EXISTS" -ForegroundColor Green
} else {
    Write-Host "   app.py: MISSING (WARNING!)" -ForegroundColor Red
}

if (Test-Path "model.py") {
    Write-Host "   model.py: EXISTS" -ForegroundColor Green
} else {
    Write-Host "   model.py: MISSING (WARNING!)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Important Notes:" -ForegroundColor Yellow
Write-Host "   On next startup, models will retrain (~30-60 seconds)" -ForegroundColor White
Write-Host "   Virtual environment .venv/ is preserved and ready to use" -ForegroundColor White
Write-Host "   Run '.\run_web_app.ps1' to start the app normally" -ForegroundColor White
Write-Host ""
Write-Host "All done! Your flask_app folder is now cleaned up." -ForegroundColor Cyan
