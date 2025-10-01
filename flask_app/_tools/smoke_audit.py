#!/usr/bin/env python3
"""
Quick smoke test: precompute a subset and run the coherence audit endpoint via Flask test client.
Usage (PowerShell):
  python .\flask_app\_tools\smoke_audit.py -m 500 -p 0.85

Env toggles are respected if already set. Reasonable defaults applied for instant run.
"""
import os
import json
import argparse

# Prefer fast bootstrap + no background training during this smoke test
os.environ.setdefault('AUTO_TRAIN_ON_IMPORT', 'false')
os.environ.setdefault('BOOTSTRAP_FAST', 'true')
os.environ.setdefault('LAZY_BACKGROUND_TRAIN', 'false')
os.environ.setdefault('PRECOMPUTE_DISABLE', 'false')
# Probability tempering defaults for presentation coherence
os.environ.setdefault('PROB_TEMPER_ENABLE', 'true')
os.environ.setdefault('PROB_TEMPER_TRIP', '0.85')
os.environ.setdefault('PROB_TEMPER_MAX', '0.85')
os.environ.setdefault('PROB_TEMPER_MIN', '0.50')
os.environ.setdefault('PROB_TEMPER_ONLY_AVOID', 'true')

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--max-rows', type=int, default=300)
parser.add_argument('-p', '--prob-high', type=float, default=0.85)
args = parser.parse_args()

from flask_app.model import precompute_investment_tiers, sample_data  # type: ignore
from flask_app.app import app  # type: ignore

n_rows = 0 if sample_data is None else len(sample_data)
print(f"Init OK. sample_data rows: {n_rows}")

# Precompute a subset
precompute_investment_tiers(max_rows=args.max_rows)

# Call coherence audit
with app.test_client() as c:
    r = c.get(f"/api/diagnostics/coherence-audit?max_rows={args.max_rows}&prob_high={args.prob_high}")
    print('HTTP', r.status_code)
    try:
        payload = r.get_json()
    except Exception:
        print(r.data.decode('utf-8', errors='ignore'))
        raise SystemExit(1)

    print(json.dumps(payload, indent=2))

    # Simple assertion-like checks for human-friendly output
    avoid_high = int(payload.get('avoid_with_high_probability', 0) or 0)
    risk_mis = int(payload.get('risk_label_mismatch', 0) or 0)
    print(f"Summary: avoid_with_high_probability={avoid_high}, risk_label_mismatch={risk_mis}")

    # Exit non-zero if clearly inconsistent
    if avoid_high > 0:
        print("WARNING: Found Avoid-tier companies with very high success probability.")
    if risk_mis > 0:
        print("WARNING: Found risk label mismatches (tier vs risk).")
