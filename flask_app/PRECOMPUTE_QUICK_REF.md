# Quick Reference: Trigger Precomputation

## ⚡ FASTEST METHOD (Just copy and paste into PowerShell):

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/admin/precompute" -Method POST -Body (@{max_rows=400; save_to_disk=$true} | ConvertTo-Json) -ContentType "application/json"
```

---

## 🐍 Or Run the Python Script:

```powershell
python trigger_precompute.py
# Press Enter to use default: 400 rows
```

---

## 🪟 Or Double-Click the Batch File:

```
trigger_precompute.bat
```

---

## ✅ Verify It Worked:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/admin/precompute/status"
```

Should show: `"available": true` and `"precomputed_count": 400`

---

## 📊 Check Score Distribution:

```powershell
python check_scoring_distribution.py
```

Expected distribution (updated Oct 2025):
- **Invest**: ~25% (highly selective)
- **Monitor**: ~45% (needs observation)
- **Avoid**: ~30% (clear red flags)

---

## 📝 Full Documentation:

- `HOW_TO_PRECOMPUTE.md` - Detailed instructions
- `SCORING_UPDATE_OCT_2025.md` - Recent scoring changes
