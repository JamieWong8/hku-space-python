import sys, os
from pathlib import Path
# Ensure lightweight import without auto-training
os.environ['AUTO_TRAIN_ON_IMPORT'] = 'false'
# Prefer real Kaggle data
os.environ['SKIP_KAGGLE'] = 'false'
# Disable precompute to keep imports fast
os.environ['PRECOMPUTE_DISABLE'] = 'true'

sys.path.append(str(Path(__file__).resolve().parent.parent))

import importlib
model = importlib.import_module('model')

# Prefer already-loaded sample_data to avoid retraining
if model.sample_data is not None and len(model.sample_data) > 0:
    df = model.sample_data.copy()
else:
    df = model.load_data()

try:
    df['region'] = df['location'].apply(model.map_location_to_region)
except Exception as e:
    print('Mapping error:', e)

other = df[df['region'] == 'Other']
vals = other['location'].astype(str).str.strip().str.upper()
counts = vals.value_counts()
print(f'Total rows: {len(df)} | Other rows: {len(other)} | Unique OTHER locations: {counts.size}')
for name, cnt in counts.items():
    print(f'{name}\t{cnt}')
