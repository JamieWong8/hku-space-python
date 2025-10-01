# Auto-Precompute Setup - Complete Guide

## ✅ What Changed?

The Flask app now **automatically triggers precomputation** when you start the server! You no longer need to manually run the precompute script in most cases.

---

## 🚀 How It Works

### Two-Stage Auto-Precompute System:

1. **Background Training Stage** (2-3 minutes after startup)
   - After background training completes, it automatically runs precomputation
   - Happens in the `_background_train_worker()` function
   - Controlled by `PRECOMPUTE_DISABLE` environment variable

2. **Startup Check Stage** (10 seconds after server starts)
   - Flask app checks if precomputed data exists
   - If not found, triggers precomputation automatically
   - Runs in a separate thread to not block the server

---

## 🎯 Quick Start (Just Run the Server!)

### Method 1: Use the New Startup Script

**Windows Batch File:**
```batch
start_with_auto_precompute.bat
```

**PowerShell:**
```powershell
.\start_with_auto_precompute.ps1
```

These scripts automatically set the right environment variables and start the server.

### Method 2: Manual Start (Recommended Settings)

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
$env:AUTO_TRAIN_ON_IMPORT='false'      # Don't block startup
$env:BOOTSTRAP_FAST='true'              # Fast bootstrap (300 companies)
$env:LAZY_BACKGROUND_TRAIN='true'       # Train in background
$env:PRECOMPUTE_DISABLE='false'         # Enable auto-precompute
& "C:/Users/jamie/OneDrive/Documents/Deal Scout/.venv/Scripts/python.exe" app.py
```

---

## 📊 What You'll See

### During Startup:

```
Initializing Deal Scout models (instant-start mode)...
Bootstrap: Auto-precomputing tiers for instant filtering...
Loading: Precomputing investment tiers for 300 companies...
Success: Precomputed tiers for 300 companies (of 300)
Bootstrap: Fast baseline models ready with precomputed tiers

Starting Deal Scout Web Application
==================================================
ML Models: Loaded and ready
Web Interface: http://localhost:5000
==================================================

Background: Training thread started
[Background training loads real 2000-company dataset...]

🔄 Waiting for background training to complete...
```

### After Background Training Completes (~2-3 minutes):

```
Background: Auto-precomputing tiers after full training...
Loading: Precomputing investment tiers for 2000 companies...
   Precomputed 400/2000 companies...
   Precomputed 800/2000 companies...
   Precomputed 1200/2000 companies...
   Precomputed 1600/2000 companies...
   Precomputed 2000/2000 companies...
Info: Applied distribution-aware score normalization
Success: Precomputed tiers for 2000 companies
Background: Auto-precompute completed successfully
Background: Full models trained and ready

✅ Precomputed data available: 2000 / 2000 companies
```

---

## ⚙️ Environment Variables

Control auto-precompute behavior with these variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PRECOMPUTE_DISABLE` | `false` | Set to `true` to disable auto-precompute |
| `AUTO_TRAIN_ON_IMPORT` | `false` | Set to `true` to train models before server starts (slow) |
| `BOOTSTRAP_FAST` | `true` | Enable fast bootstrap with 300 sample companies |
| `LAZY_BACKGROUND_TRAIN` | `true` | Train full models in background thread |

### Examples:

**Disable Auto-Precompute (Old Behavior):**
```powershell
$env:PRECOMPUTE_DISABLE='true'
python app.py
```

**Force Synchronous Training (Slower Startup but Immediate Availability):**
```powershell
$env:AUTO_TRAIN_ON_IMPORT='true'
python app.py
```

---

## 🔍 Verify It's Working

### Option 1: Check Server Logs

Look for these messages in console output:
- ✅ `"Background: Auto-precompute completed successfully"`
- ✅ `"Precomputed data available: 2000 / 2000 companies"`

### Option 2: Check Status API

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/admin/precompute/status"
```

**Expected Output:**
```json
{
  "available": true,
  "precomputed_count": 2000,
  "total_companies": 2000,
  "coverage_percentage": 100.0,
  "message": "Precomputed data is available"
}
```

### Option 3: Check Company Scores in Browser

1. Open `http://localhost:5000`
2. Click "Evaluate Companies" tab
3. **You should see varied scores** (not all 50%!)
   - Some companies with 70-85% (Invest)
   - Some companies with 45-60% (Monitor)
   - Some companies with 20-40% (Avoid)

---

## ⏱️ Timeline

| Time | What's Happening |
|------|------------------|
| **0:00** | Server starts, fast bootstrap (300 companies) |
| **0:05** | Server is ready for requests (with bootstrap data) |
| **0:10** | Background training starts (2000 companies) |
| **2:30** | Background training completes |
| **2:30** | Auto-precompute begins (2000 companies) |
| **4:30** | Auto-precompute completes |
| **4:30** | ✅ All companies have real scores! |

**Total Wait Time:** ~4-5 minutes from server start to full precomputation

**Server Available:** Immediately (but shows 50% scores for first 4-5 minutes)

---

## 🐛 Troubleshooting

### Problem: Still seeing all 50% scores after 5 minutes

**Diagnosis:**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/admin/precompute/status"
```

If `"available": false`:

1. **Check server logs** for error messages
2. **Manually trigger precompute**:
   ```powershell
   python trigger_precompute.py
   ```
3. **Restart server** with explicit settings:
   ```powershell
   $env:PRECOMPUTE_DISABLE='false'
   python app.py
   ```

### Problem: Server taking too long to start

**Cause:** Auto-precompute may be running synchronously

**Solution:** Use background mode (default):
```powershell
$env:AUTO_TRAIN_ON_IMPORT='false'
$env:LAZY_BACKGROUND_TRAIN='true'
python app.py
```

### Problem: Precomputation fails with errors

**Diagnosis:** Check server logs for stack traces

**Workaround:** Disable auto-precompute and run manually:
```powershell
$env:PRECOMPUTE_DISABLE='true'
python app.py

# In another terminal:
python trigger_precompute.py
```

---

## 📝 For Developers

### Code Locations:

1. **Background Training Auto-Precompute**
   - File: `model.py`
   - Function: `_background_train_worker()`
   - Lines: ~3040-3050
   - Triggers after `train_models()` completes

2. **Startup Check Auto-Precompute**
   - File: `app.py`
   - Function: `ensure_precomputed_data()`
   - Lines: ~1825-1850
   - Runs in daemon thread 10 seconds after server starts

3. **Manual Precompute API**
   - Endpoint: `POST /api/admin/precompute`
   - Still available for manual triggering

### How to Disable Completely:

```python
# In model.py line 3033:
_precompute_after = False  # Hard-code to False

# In app.py line 1823:
# Comment out the entire ensure_precomputed_data() section
```

---

## 🎉 Summary

**✅ Auto-precompute is now enabled by default!**

**Just run the server and wait ~4-5 minutes. Everything happens automatically!**

**Old way:**
```powershell
python app.py
# Wait...
python trigger_precompute.py  # ← Had to do this manually
# Wait...
# Finally ready!
```

**New way:**
```powershell
python app.py
# Wait 4-5 minutes...
# ✅ Ready! Everything automatic!
```

---

## 📚 Related Files

- **`start_with_auto_precompute.bat`** - Windows batch starter
- **`start_with_auto_precompute.ps1`** - PowerShell starter
- **`trigger_precompute.py`** - Manual trigger (still available)
- **`HOW_TO_PRECOMPUTE.md`** - Original manual instructions
- **`PRECOMPUTE_QUICK_REF.md`** - Quick reference

---

**Last Updated:** October 1, 2025
**Feature Added:** Auto-precompute on server startup
**Status:** ✅ Fully Implemented and Tested
