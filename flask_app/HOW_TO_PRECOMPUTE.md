# How to Manually Trigger Precomputation

After starting the Flask server, you need to trigger precomputation to populate the attractiveness scores and investment tiers. Here are all the methods:

---

## Prerequisites

1. **Flask server must be running** at `http://localhost:5000`
2. **Models must be trained** (happens automatically on startup)

---

## Method 1: PowerShell Command ⭐ RECOMMENDED

Copy and paste this into PowerShell:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/admin/precompute" -Method POST -Body (@{max_rows=2000; save_to_disk=$true} | ConvertTo-Json) -ContentType "application/json"
```

**Expected Output:**
```json
{
  "status": "ok",
  "counts": {
    "total_scored": 2000,
    "invest": 1418,
    "monitor": 382,
    "avoid": 200
  },
  "saved_to_cache": true,
  "data_signature": "...",
  "build_id": "..."
}
```

---

## Method 2: Using curl (if installed)

```bash
curl -X POST http://localhost:5000/api/admin/precompute \
  -H "Content-Type: application/json" \
  -d '{"max_rows": 2000, "save_to_disk": true}'
```

---

## Method 3: Browser Developer Console

1. Open your browser to `http://localhost:5000`
2. Press `F12` to open Developer Tools
3. Go to the **Console** tab
4. Paste and run:

```javascript
fetch('http://localhost:5000/api/admin/precompute', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({max_rows: 2000, save_to_disk: true})
})
.then(r => r.json())
.then(data => console.log(data))
```

---

## Method 4: Postman or Similar API Tool

**Request Settings:**
- **Method:** `POST`
- **URL:** `http://localhost:5000/api/admin/precompute`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
```json
{
  "max_rows": 2000,
  "save_to_disk": true
}
```

---

## Method 5: Python Script

Create a file `trigger_precompute.py`:

```python
import requests
import json

response = requests.post(
    'http://localhost:5000/api/admin/precompute',
    json={'max_rows': 2000, 'save_to_disk': True}
)

print(json.dumps(response.json(), indent=2))
```

Run it:
```powershell
python trigger_precompute.py
```

---

## Verify It Worked

Check the status:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/admin/precompute/status" -Method GET
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

---

## Check Company Scores

View first 3 companies with scores:

```powershell
(Invoke-RestMethod -Uri "http://localhost:5000/api/companies?page=1&per_page=3").companies | 
  Select-Object company_name, attractiveness_score, investment_tier | 
  Format-Table
```

**Expected Output:**
```
company_name           attractiveness_score investment_tier
------------           -------------------- ---------------
#waywire                         73.904648 Invest
&TV Communications               75.098042 Invest
'Rock' Your Paper                37.422071 Avoid
```

---

## Troubleshooting

### "Unable to connect to the remote server"
- **Cause:** Flask server is not running
- **Solution:** Start the server first:
  ```powershell
  cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
  $env:AUTO_TRAIN_ON_IMPORT='false'
  & "C:/Users/jamie/OneDrive/Documents/Deal Scout/.venv/Scripts/python.exe" app.py
  ```

### "available": false or "precomputed_count": 0
- **Cause:** Precomputation hasn't been triggered yet
- **Solution:** Run Method 1 (PowerShell command)

### All companies still showing 50% Monitor
- **Cause:** Precomputation failed or server restarted without loading cache
- **Solution:** 
  1. Check server logs for errors
  2. Trigger precomputation again
  3. Refresh your browser

### Precomputation takes too long
- **Cause:** Computing 2000 companies can take 2-5 minutes
- **Solution:** Use fewer companies for testing:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:5000/api/admin/precompute" -Method POST -Body (@{max_rows=500; save_to_disk=$true} | ConvertTo-Json) -ContentType "application/json"
  ```

---

## Parameters

### `max_rows` (optional, default: all)
- Number of companies to precompute
- Use lower numbers for faster testing
- Examples: 100, 500, 1000, 2000

### `save_to_disk` (optional, default: true)
- Whether to save precomputed data to cache
- Set to `false` for temporary testing
- Set to `true` to persist across restarts

---

## When to Trigger Precomputation

You need to trigger it:

1. **First time** after starting the server
2. **After model retraining** (if models change significantly)
3. **After data updates** (if new companies are added)
4. **After cache clearing** (if you used `/api/admin/clear-cache`)

You do NOT need to trigger it:

- Every time you load the page
- Between page refreshes
- When filtering or searching companies
- After server restart (if cached data exists)

---

## Quick Start Checklist

- [ ] Start Flask server
- [ ] Wait for "Background: Full models trained and ready"
- [ ] Run precomputation command (Method 1)
- [ ] Wait 2-5 minutes for completion
- [ ] Verify status shows `"available": true`
- [ ] Refresh browser and check scores are varied
- [ ] Test filtering by Investment Tier

---

**That's it!** After precomputation completes, all companies will show their correct scores and tiers.
