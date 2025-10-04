# 🧹 Flask App Cleanup Guide

## Issue: Large File Size

**Total Unnecessary Files:** ~1,500 MB (1.5 GB)  
**Recommended for Deletion:** 5 directories + cache files

---

## 📊 Size Analysis

| Directory | Size | Can Delete? | Reason |
|-----------|------|-------------|--------|
| `venv/` | **733 MB** | ✅ YES | Duplicate virtual environment |
| `.venv/` | **714 MB** | ✅ YES | Duplicate virtual environment (keep only one) |
| `.model_cache/` | **55 MB** | ✅ YES | Auto-regenerates on startup |
| `kaggle_data/` | **12 MB** | ⚠️ OPTIONAL | Re-downloads from Kaggle if needed |
| `__pycache__/` | **0.5 MB** | ✅ YES | Python bytecode cache (auto-regenerates) |
| `.pytest_cache/` | **< 1 MB** | ✅ YES | Test cache (auto-regenerates) |
| `debug_log.txt` | **< 1 MB** | ✅ YES | Old debug logs |

**Total Savings:** ~1,500 MB (1.5 GB) if all deleted

---

## ⚠️ Key Finding: Duplicate Virtual Environments

You have **TWO virtual environments** installed:
1. `venv/` (733 MB) - Standard name
2. `.venv/` (714 MB) - Hidden directory (dot prefix)

**Why this happened:**
- Different installation commands create different venv names
- `python -m venv venv` creates `venv/`
- `python -m venv .venv` creates `.venv/`
- Both contain the same dependencies

**Recommendation:** Keep only ONE virtual environment (preferably `.venv`)

---

## 🗑️ Safe to Delete (Recommended)

### 1. Delete Duplicate `venv/` Directory
**Size:** 733 MB  
**Why Safe:** You have `.venv/` as a duplicate  
**Regenerates:** Yes (via `python -m venv venv`)

### 2. Delete `.model_cache/` Directory
**Size:** 55 MB  
**Why Safe:** Auto-regenerates on first app startup  
**Regenerates:** Yes (takes 30-60 seconds on first run)  
**Contents:**
- Trained ML model files (.pkl)
- Precomputed tier data
- Analysis cache

### 3. Delete `__pycache__/` Directory
**Size:** 0.5 MB  
**Why Safe:** Python bytecode cache  
**Regenerates:** Yes (automatically when .py files run)

### 4. Delete `.pytest_cache/` Directory
**Size:** < 1 MB  
**Why Safe:** Test runner cache  
**Regenerates:** Yes (when tests run)

### 5. Delete `debug_log.txt`
**Size:** < 1 MB  
**Why Safe:** Old debug output  
**Regenerates:** No (but not needed)

---

## ⚠️ Optional Deletions

### 6. Delete `kaggle_data/` Directory
**Size:** 12 MB  
**Why Optional:** Contains cached Kaggle dataset (investments_VC.csv)  
**Regenerates:** Yes (downloads from Kaggle on next run)  
**Tradeoff:** 
- ✅ Saves 12 MB
- ❌ Requires internet + Kaggle credentials to re-download
- ❌ Takes 10-20 seconds on first startup after deletion

**Recommendation:** Delete if you have Kaggle credentials configured, keep if offline or no credentials

---

## 📋 Cleanup Script

Save this as `cleanup_flask_app.ps1`:

```powershell
# Flask App Cleanup Script
# Removes unnecessary files and duplicate virtual environments

Write-Host "🧹 Flask App Cleanup Script" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""

$flaskAppPath = "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
cd $flaskAppPath

# Calculate initial size
$initialSize = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "📊 Initial size: $([math]::Round($initialSize, 2)) MB" -ForegroundColor Yellow
Write-Host ""

# 1. Delete duplicate venv/ (keeping .venv/)
if (Test-Path "venv") {
    $venvSize = (Get-ChildItem "venv" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "🗑️  Deleting venv/ ($([math]::Round($venvSize, 2)) MB)..." -ForegroundColor Red
    Remove-Item -Path "venv" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Deleted venv/" -ForegroundColor Green
} else {
    Write-Host "ℹ️  venv/ not found (already clean)" -ForegroundColor Gray
}

# 2. Delete .model_cache/
if (Test-Path ".model_cache") {
    $cacheSize = (Get-ChildItem ".model_cache" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "🗑️  Deleting .model_cache/ ($([math]::Round($cacheSize, 2)) MB)..." -ForegroundColor Red
    Remove-Item -Path ".model_cache" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Deleted .model_cache/" -ForegroundColor Green
} else {
    Write-Host "ℹ️  .model_cache/ not found" -ForegroundColor Gray
}

# 3. Delete __pycache__/
if (Test-Path "__pycache__") {
    Write-Host "🗑️  Deleting __pycache/..." -ForegroundColor Red
    Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Deleted __pycache/" -ForegroundColor Green
}

# 4. Delete .pytest_cache/
if (Test-Path ".pytest_cache") {
    Write-Host "🗑️  Deleting .pytest_cache/..." -ForegroundColor Red
    Remove-Item -Path ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Deleted .pytest_cache/" -ForegroundColor Green
}

# 5. Delete debug_log.txt
if (Test-Path "debug_log.txt") {
    Write-Host "🗑️  Deleting debug_log.txt..." -ForegroundColor Red
    Remove-Item -Path "debug_log.txt" -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Deleted debug_log.txt" -ForegroundColor Green
}

# Optional: Delete kaggle_data/ (uncomment if desired)
# if (Test-Path "kaggle_data") {
#     $kaggleSize = (Get-ChildItem "kaggle_data" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
#     Write-Host "🗑️  Deleting kaggle_data/ ($([math]::Round($kaggleSize, 2)) MB)..." -ForegroundColor Red
#     Remove-Item -Path "kaggle_data" -Recurse -Force -ErrorAction SilentlyContinue
#     Write-Host "✅ Deleted kaggle_data/" -ForegroundColor Green
# }

Write-Host ""
Write-Host "🎉 Cleanup Complete!" -ForegroundColor Green
Write-Host ""

# Calculate final size
$finalSize = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
$saved = $initialSize - $finalSize

Write-Host "📊 Final size: $([math]::Round($finalSize, 2)) MB" -ForegroundColor Yellow
Write-Host "💾 Space saved: $([math]::Round($saved, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Note: On next startup, models will retrain (~30-60 seconds)" -ForegroundColor Yellow
Write-Host "✅ Virtual environment .venv/ is preserved and ready to use" -ForegroundColor Green
```

---

## 🚀 How to Clean Up

### Option 1: Run PowerShell Script (Recommended)
```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\cleanup_flask_app.ps1
```

### Option 2: Manual Cleanup
```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"

# Delete duplicate venv
Remove-Item -Path "venv" -Recurse -Force

# Delete model cache
Remove-Item -Path ".model_cache" -Recurse -Force

# Delete Python cache
Remove-Item -Path "__pycache__" -Recurse -Force

# Delete pytest cache
Remove-Item -Path ".pytest_cache" -Recurse -Force

# Delete debug log
Remove-Item -Path "debug_log.txt" -Force

# Optional: Delete Kaggle data
# Remove-Item -Path "kaggle_data" -Recurse -Force
```

---

## 🔄 After Cleanup

### First Startup After Cleanup
When you run the app for the first time after cleanup:

1. **Models will retrain** (~30-60 seconds)
   - Normal behavior
   - Cached models were deleted
   - New cache will be created

2. **Python cache regenerates** (automatic, instant)
   - `__pycache__/` directories recreate
   - No action needed

3. **Kaggle data re-downloads** (if deleted)
   - Only if you deleted `kaggle_data/`
   - Requires internet + Kaggle credentials
   - Takes 10-20 seconds

### Normal Startup
```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\run_web_app.ps1
```

The script will:
- Use `.venv/` virtual environment (the one we kept)
- Retrain models and cache them
- Start normally

---

## 📁 What to Keep

### Essential Files (DO NOT DELETE)
- ✅ `.venv/` - Virtual environment (keep this one)
- ✅ `app.py` - Flask application
- ✅ `model.py` - ML models
- ✅ `requirements.txt` - Dependencies
- ✅ `run_web_app.ps1` - Startup script
- ✅ `static/` - CSS, JS, images
- ✅ `templates/` - HTML templates
- ✅ `kaggle.json` - Kaggle credentials (if configured)
- ✅ `README.md` - Documentation
- ✅ `_tools/` - Utility scripts

### Can Delete (Will Regenerate)
- 🗑️ `venv/` - Duplicate virtual environment
- 🗑️ `.model_cache/` - ML model cache
- 🗑️ `__pycache__/` - Python bytecode
- 🗑️ `.pytest_cache/` - Test cache
- 🗑️ `debug_log.txt` - Old logs

### Optional Deletion
- ⚠️ `kaggle_data/` - Kaggle dataset cache (12 MB)

---

## 🛡️ Gitignore Update

Add these to your `.gitignore` to prevent committing large files:

```gitignore
# Virtual environments
venv/
.venv/
env/
ENV/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Model cache
.model_cache/

# Test cache
.pytest_cache/
.coverage
htmlcov/

# Logs
debug_log.txt
*.log

# Kaggle data (optional - can keep or remove)
kaggle_data/

# IDE
.vscode/
.idea/
```

---

## 📊 Expected Results

### Before Cleanup
```
flask_app/
├── venv/           733 MB  ❌ Duplicate
├── .venv/          714 MB  ✅ Keep
├── .model_cache/    55 MB  ❌ Delete
├── kaggle_data/     12 MB  ⚠️ Optional
├── __pycache__/    0.5 MB  ❌ Delete
├── Other files      ~1 MB
└── TOTAL:        ~1,515 MB
```

### After Cleanup
```
flask_app/
├── .venv/          714 MB  ✅ Virtual environment
├── kaggle_data/     12 MB  ✅ Cached data (optional)
├── static/         0.2 MB  ✅ Assets
├── templates/     0.09 MB  ✅ HTML
├── Other files      ~1 MB  ✅ Code
└── TOTAL:          ~727 MB (52% reduction!)
```

**Space Saved:** ~788 MB (1,515 → 727 MB)  
**Percentage Saved:** 52%

---

## ⚡ Quick Commands

### Check folder sizes
```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
Get-ChildItem -Directory | ForEach-Object { 
    $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    [PSCustomObject]@{Folder=$_.Name; 'Size(MB)'=[math]::Round($size, 2)} 
} | Sort-Object 'Size(MB)' -Descending | Format-Table -AutoSize
```

### Quick delete commands
```powershell
# Delete duplicate venv only
Remove-Item -Path "venv" -Recurse -Force

# Delete all cache directories
Remove-Item -Path ".model_cache", "__pycache__", ".pytest_cache" -Recurse -Force
```

---

## 🎯 Recommendation Summary

**Immediate Actions (Safe):**
1. ✅ Delete `venv/` (733 MB) - duplicate virtual environment
2. ✅ Delete `.model_cache/` (55 MB) - regenerates on startup
3. ✅ Delete `__pycache__/` (0.5 MB) - Python cache
4. ✅ Delete `.pytest_cache/` - Test cache
5. ✅ Delete `debug_log.txt` - Old logs

**Total Savings:** ~788 MB (52% reduction)

**Optional (if you have Kaggle credentials):**
6. ⚠️ Delete `kaggle_data/` (12 MB) - re-downloads on startup

**Do NOT Delete:**
- ❌ `.venv/` - Your active virtual environment
- ❌ Any `.py` files
- ❌ `static/` or `templates/`
- ❌ `requirements.txt`
- ❌ `kaggle.json` (if configured)

---

## 🔍 Troubleshooting

### Problem: App won't start after cleanup
**Solution:**
```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
# Activate virtual environment
.\.venv\Scripts\Activate.ps1
# Reinstall dependencies (if needed)
pip install -r requirements.txt
# Run normally
.\run_web_app.ps1
```

### Problem: "venv not found" error
**Solution:** You deleted the wrong venv. Recreate it:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Problem: Models training takes long on first startup
**Solution:** This is normal after deleting `.model_cache/`. Wait 30-60 seconds. Subsequent startups will be fast.

---

**Ready to clean up? Run the PowerShell script or use the manual commands above!** 🧹✨
