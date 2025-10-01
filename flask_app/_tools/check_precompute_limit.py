#!/usr/bin/env python3
"""
Quick check that PRECOMPUTE_MAX_ROWS is honored.

Usage:
  Set environment variables before running:
    - PRECOMPUTE_MAX_ROWS: the desired limit (e.g., 20)
    - SKIP_KAGGLE=true to avoid network fetches

This script will import model (auto-trains and precomputes on import) and
print the count of rows with non-empty precomputed tier values.
"""
import os, sys

here = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(here, os.pardir))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Ensure auto train and precompute are enabled for this check and set limits before import
os.environ['AUTO_TRAIN_ON_IMPORT'] = 'true'
os.environ['PRECOMPUTE_DISABLE'] = 'false'
os.environ.setdefault('SKIP_KAGGLE', 'true')

# Optional CLI arg to set limit explicitly
if len(sys.argv) > 1 and sys.argv[1].strip():
    os.environ['PRECOMPUTE_MAX_ROWS'] = sys.argv[1].strip()

limit = os.environ.get('PRECOMPUTE_MAX_ROWS', '').strip()
print('[CHECK] PRECOMPUTE_MAX_ROWS env =', repr(limit))

import model

sd = model.sample_data
if sd is None or len(sd) == 0:
    print('[CHECK] sample_data is empty; nothing to verify')
    sys.exit(0)

pre_cols = ['precomputed_attractiveness_score','precomputed_investment_tier_norm']
present = all(c in sd.columns for c in pre_cols)
non_empty = (sd['precomputed_investment_tier_norm'].astype(str).str.len() > 0).sum() if present else 0
total = len(sd)
print(f'[CHECK] sample_data rows: {total}; precompute cols present: {present}; non-empty precomputed rows: {non_empty}')

try:
    lim_int = int(limit) if limit else None
except Exception:
    lim_int = None

if lim_int is None:
    print('[CHECK] No limit set (or invalid). Expect non_empty to be close to total (subject to data filters).')
else:
    print(f'[CHECK] Limit set to {lim_int}. Expect non_empty <= {lim_int}.')
