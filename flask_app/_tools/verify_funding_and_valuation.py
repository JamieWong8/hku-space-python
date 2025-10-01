#!/usr/bin/env python3
"""
Verify that:
- funding_amount_usd is populated from funding_total_usd (non-zero)
- valuation_usd is derived when funding exists (non-zero)
- /api/companies excludes rows without funding_total_usd

Runs without using PowerShell by importing the Flask app directly.
"""
import os
import sys


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.abspath(os.path.join(here, os.pardir))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # Ensure no precompute limit for this run
    os.environ["PRECOMPUTE_MAX_ROWS"] = ""
    # Prefer Kaggle/local data path as configured in model
    try:
        import app as appmod
        from model import sample_data
    except Exception as e:
        print(f"[VERIFY] FAIL: Import error: {e}")
        return 2

    client = appmod.app.test_client()

    # Pull a few pages to validate consistently
    total_checked = 0
    total_bad_funding = 0
    total_bad_valuation = 0

    for page in range(1, 4):
        r = client.get(f"/api/companies?per_page=25&page={page}")
        if r.status_code != 200:
            print(f"[VERIFY] FAIL: /api/companies status={r.status_code} on page {page}")
            return 3
        data = r.get_json(force=True)
        comps = data.get("companies", [])
        for c in comps:
            total_checked += 1
            f = float(c.get("funding_amount_usd", 0) or 0)
            v = float(c.get("valuation_usd", 0) or 0)
            if f <= 0:
                total_bad_funding += 1
            if f > 0 and v <= 0:
                total_bad_valuation += 1

    # Check sample_data flag presence (optional diagnostic)
    has_flag = False
    flag_true_count = None
    try:
        if sample_data is not None and 'has_funding_total_usd' in sample_data.columns:
            has_flag = True
            flag_true_count = int(sample_data['has_funding_total_usd'].sum())
    except Exception:
        pass

    if total_checked == 0:
        print("[VERIFY] FAIL: No companies returned by API")
        return 4

    print(f"[VERIFY] Checked: {total_checked} cards; bad_funding={total_bad_funding}; bad_valuation={total_bad_valuation}; flag_present={has_flag}; flag_true_count={flag_true_count}")

    # All cards should have funding>0 and valuation>0 as they are excluded otherwise
    if total_bad_funding > 0:
        print("[VERIFY] FAIL: Some cards have missing/zero funding_amount_usd; expected exclusion of such rows")
        return 5
    if total_bad_valuation > 0:
        print("[VERIFY] FAIL: Some cards have zero valuation despite positive funding")
        return 6

    print("[VERIFY] PASS: Funding and valuation populated; filter exclusion working; no precompute limit set.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
