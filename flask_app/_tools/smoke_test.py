#!/usr/bin/env python3
"""
Lightweight smoke test for Deal Scout Flask app using Flask's test client.
Verifies diagnostics endpoint availability, grouped region filters in /api/companies,
and basic pagination behavior with and without a region filter.
"""
import os
import sys
import json
from typing import Any, Dict


def main() -> int:
    # Ensure we can import the app module from the flask_app folder
    here = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.abspath(os.path.join(here, os.pardir))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    try:
        import app as appmod
    except Exception as e:
        print(f"[SMOKE] FAIL: Could not import app.py from {app_dir}: {e}")
        return 2

    client = appmod.app.test_client()

    # 1) Diagnostics: /__build
    r = client.get('/__build')
    if r.status_code != 200:
        print(f"[SMOKE] FAIL: /__build status={r.status_code}")
        return 3
    try:
        build = r.get_json(force=True)
    except Exception:
        build = json.loads(r.get_data(as_text=True))
    print(f"[SMOKE] OK: __build -> {build}")

    # 2) Basic companies list and filters
    r = client.get('/api/companies?per_page=5')
    if r.status_code != 200:
        print(f"[SMOKE] FAIL: /api/companies status={r.status_code}")
        return 4
    payload: Dict[str, Any] = r.get_json(force=True)
    filters = payload.get('filters', {})
    regions = filters.get('regions', [])
    if not regions:
        print("[SMOKE] FAIL: filters.regions missing or empty; expected grouped region list")
        return 5
    if 'Other' in regions:
        print("[SMOKE] FAIL: filters.regions should not include 'Other'")
        return 6
    print(f"[SMOKE] OK: regions -> {regions}")

    # 3) Region filtering smoke test (pick the first available region)
    test_region = regions[0]
    r2 = client.get(f'/api/companies?region={test_region}&per_page=5')
    if r2.status_code != 200:
        print(f"[SMOKE] FAIL: /api/companies?region=... status={r2.status_code}")
        return 7
    payload2: Dict[str, Any] = r2.get_json(force=True)
    companies = payload2.get('companies', [])
    if not isinstance(companies, list):
        print("[SMOKE] FAIL: companies field missing or not a list")
        return 8
    print(f"[SMOKE] OK: region filter '{test_region}' returned {len(companies)} companies (page size)")

    # If region is present on company objects, optionally verify
    region_field_present = any(isinstance(c, dict) and 'region' in c for c in companies)
    if region_field_present:
        bad = [c for c in companies if c.get('region') != test_region]
        if bad:
            print(f"[SMOKE] FAIL: Some companies not in requested region '{test_region}': {len(bad)} mismatches")
            return 9
        print("[SMOKE] OK: all returned companies match the requested region")

    print("[SMOKE] ALL CHECKS PASSED")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
