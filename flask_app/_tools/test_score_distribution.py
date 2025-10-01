import os
import importlib
import numpy as np
import sys
from pathlib import Path

# Ensure parent (flask_app) directory is on sys.path so we can import model.py
PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))


def main():
    # Keep things fast and deterministic for this check
    os.environ.setdefault('AUTO_TRAIN_ON_IMPORT', 'false')
    os.environ.setdefault('CACHE_MODELS', 'false')
    os.environ.setdefault('SKIP_KAGGLE', 'true')
    os.environ.setdefault('PRECOMPUTE_DISABLE', 'true')

    m = importlib.import_module('model')
    m.train_models()

    # Work on a copy to avoid mutating the main df inadvertently
    m.precompute_investment_tiers(max_rows=400)
    sd = m.sample_data

    if 'precomputed_attractiveness_score' in sd.columns:
        desc = sd['precomputed_attractiveness_score'].dropna().describe()
        print('SCORES:')
        print(desc.to_string())

    if 'precomputed_investment_tier_norm' in sd.columns:
        vc = sd['precomputed_investment_tier_norm'].value_counts(dropna=False)
        print('TIERS:')
        print(vc.to_string())


if __name__ == '__main__':
    main()
