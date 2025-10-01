# Score Consistency Fix - All Tiers Showing as 50% Monitor

> **📝 NOTE:** This document describes a historical bug fix. For the most recent scoring updates and tier thresholds (65/50), see [../OCTOBER_2025_UPDATES.md](../OCTOBER_2025_UPDATES.md).

## Problem

The Evaluate Companies tab was showing all companies with the same score (50%) and tier (Monitor), regardless of their actual calculated scores. However, clicking "Analyze" on individual companies showed the correct scores. For example, &TV Communications showed:
- **Company List**: 50% Monitor
- **Analysis Dashboard**: 75.1% Invest (correct)

This indicated the scoring was working correctly but the company list wasn't accessing the precomputed scores.

## Root Cause

The issue was caused by **Python's import binding behavior**:

1. In `app.py`, endpoints were using `from model import sample_data` inside each function
2. This creates a local binding to the `sample_data` object at the time of import
3. When `model.py` later reassigns `sample_data` (using `global sample_data`) during precomputation, the local bindings in `app.py` still point to the OLD DataFrame
4. The old DataFrame doesn't have the precomputed columns, so all companies got default values (50%, Monitor)

### Technical Explanation

```python
# In model.py (simplified)
sample_data = None  # Initial value

def precompute_investment_tiers():
    global sample_data
    # Add precomputed columns to sample_data
    sample_data['precomputed_attractiveness_score'] = ...
    sample_data['precomputed_investment_tier'] = ...

# In app.py (old code - WRONG)
@app.route('/api/companies')
def api_companies():
    from model import sample_data  # Gets reference to INITIAL sample_data
    # Later, when precompute runs, this local variable doesn't get updated!
    for company in sample_data:  # Missing precomputed columns!
        score = company.get('precomputed_attractiveness_score', 50.0)  # Always 50.0
```

## Solution

Changed all endpoint functions to access `sample_data` through the `model` module reference instead of importing it directly:

```python
# At module level
import model
from model import (...other functions...)

# In endpoints (NEW - CORRECT)
@app.route('/api/companies')
def api_companies():
    # Access dynamically through module reference
    if model.sample_data is None:
        return error()
    
    for company in model.sample_data:  # Gets CURRENT sample_data with precomputed columns!
        score = company.get('precomputed_attractiveness_score', 50.0)  # Real scores!
```

## Changes Made

1. **app.py (line 31)**: Added `import model` at module level
2. **app.py (all endpoints)**: Replaced `from model import sample_data` with `model.sample_data`
3. **app.py (all endpoints)**: Replaced `from model import data_source` with `model.data_source`
4. **app.py (get_cached_filter_options)**: Updated to use `model.sample_data`, `model.grouped_industries`, `model.regions`

Total lines changed: ~30 functions updated across the entire file

## Testing

### Before Fix
```json
{
  "company_name": "&TV Communications",
  "attractiveness_score": 50.0,
  "investment_tier": "Monitor"
}
```

### After Fix
```json
{
  "company_name": "&TV Communications",
  "attractiveness_score": 75.09804164805149,
  "investment_tier": "Invest"
}
```

### Consistency Verification
- **Company List**: 75.1% Invest ✓
- **Analysis Dashboard**: 75.1% Invest ✓
- **Scores Match**: YES ✓

## Important Notes

1. **Precomputation Required**: The fix only works if precomputed data exists. If the server starts and shows "Skipping precompute", you need to manually trigger it:
   ```bash
   POST http://localhost:5000/api/admin/precompute
   Body: {"max_rows": 2000, "save_to_disk": true}
   ```

2. **Why Precompute Was Skipped**: Check model.py for `PRECOMPUTE_DISABLE` environment variable or conditions that skip auto-precompute

3. **Verify Precomputation Status**:
   ```bash
   GET http://localhost:5000/api/admin/precompute/status
   ```
   Should show `"available": true` and `"precomputed_count": 2000`

## Related Files

- `flask_app/app.py` - All API endpoints updated
- `flask_app/model.py` - Precomputation logic (no changes needed)
- `flask_app/fix_imports.py` - Script used to automate the fix
- `flask_app/check_precomputed.py` - Diagnostic script to verify precomputed columns exist

## Lessons Learned

1. **Never import mutable globals from other modules** - always access them through the module reference
2. **Use `module.variable` instead of `from module import variable`** when the variable can be reassigned
3. **Add diagnostic endpoints** to check if precomputed data is available (e.g., `/api/admin/precompute/status`)
4. **Log precomputation status** at server startup to catch issues early

## Prevention

To prevent this issue in the future:

1. Always use `model.sample_data` instead of importing it directly
2. Add startup checks to verify precomputed columns exist
3. Add UI warnings when precomputed data is unavailable
4. Ensure auto-precompute runs reliably after training completes

---

**Status**: ✅ **FIXED** - All scores now consistent between company list and analysis dashboard
**Date**: 2025-10-01
**Impact**: Critical UX issue resolved - users now see accurate scores immediately
