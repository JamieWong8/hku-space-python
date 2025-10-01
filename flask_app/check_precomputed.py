#!/usr/bin/env python3
"""Check if precomputed columns exist in sample_data"""
import sys
import os

# Ensure model can be imported
sys.path.insert(0, os.path.dirname(__file__))

from model import sample_data
import pandas as pd

print("=== Checking Precomputed Data ===\n")

# Check for precomputed columns
precomputed_cols = [col for col in sample_data.columns if 'precomputed' in col]
print(f"Precomputed columns found: {precomputed_cols}")
print(f"Total columns: {len(sample_data.columns)}")
print()

# Show first 5 companies
print("First 5 companies precomputed values:")
print("-" * 80)
for idx in range(min(5, len(sample_data))):
    row = sample_data.iloc[idx]
    print(f"\nCompany: {row.get('company_name', 'Unknown')}")
    print(f"  ID: {row.get('company_id', 'Unknown')}")
    
    if 'precomputed_attractiveness_score' in sample_data.columns:
        score = row.get('precomputed_attractiveness_score')
        print(f"  Attractiveness Score: {score}")
    else:
        print(f"  Attractiveness Score: COLUMN MISSING")
    
    if 'precomputed_investment_tier' in sample_data.columns:
        tier = row.get('precomputed_investment_tier')
        print(f"  Investment Tier: {tier}")
    else:
        print(f"  Investment Tier: COLUMN MISSING")
    
    if 'precomputed_investment_tier_norm' in sample_data.columns:
        tier_norm = row.get('precomputed_investment_tier_norm')
        print(f"  Investment Tier (normalized): {tier_norm}")
    else:
        print(f"  Investment Tier (normalized): COLUMN MISSING")

print("\n" + "=" * 80)
print(f"Total companies in dataset: {len(sample_data)}")

# Check if any non-null values exist
if 'precomputed_attractiveness_score' in sample_data.columns:
    non_null_count = sample_data['precomputed_attractiveness_score'].notna().sum()
    print(f"Companies with precomputed scores: {non_null_count} / {len(sample_data)}")
    if non_null_count > 0:
        print(f"Score range: {sample_data['precomputed_attractiveness_score'].min():.2f} - {sample_data['precomputed_attractiveness_score'].max():.2f}")
else:
    print("WARNING: precomputed_attractiveness_score column does not exist!")

print("=" * 80)
