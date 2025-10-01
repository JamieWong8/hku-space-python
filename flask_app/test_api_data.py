#!/usr/bin/env python3
"""Test what the API actually returns for companies"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from model import sample_data
import pandas as pd

print("=== Testing API Data Extraction ===\n")

# Simulate what the API does
page_companies = sample_data.head(5)

print("Columns in page_companies:")
print([col for col in page_companies.columns if 'precomputed' in col])
print()

# Test accessing data for first company
company = page_companies.iloc[0]

print(f"Testing data access for: {company.get('company_name')}\n")

# Test 1: Check if columns exist
print("Column existence checks:")
print(f"  'precomputed_attractiveness_score' in columns: {'precomputed_attractiveness_score' in page_companies.columns}")
print(f"  'precomputed_investment_tier' in columns: {'precomputed_investment_tier' in page_companies.columns}")
print()

# Test 2: Try to get values
print("Direct value access:")
val1 = company.get('precomputed_attractiveness_score', None)
print(f"  company.get('precomputed_attractiveness_score'): {val1}")
print(f"  Type: {type(val1)}")
print(f"  pd.notna(val): {pd.notna(val1)}")
print()

val2 = company.get('precomputed_investment_tier', None)
print(f"  company.get('precomputed_investment_tier'): {val2}")
print(f"  Type: {type(val2)}")
print()

# Test 3: Build company dict as API does
print("Building company_dict as API does:")
company_dict = {
    'company_id': str(company.get('company_id', '')),
    'company_name': str(company.get('company_name', '')),
}

# Simulate the enrichment logic
if 'precomputed_attractiveness_score' in page_companies.columns:
    val = company.get('precomputed_attractiveness_score', None)
    print(f"  Found precomputed_attractiveness_score column")
    print(f"  Value: {val}")
    print(f"  pd.notna(val): {pd.notna(val)}")
    if val is not None and pd.notna(val):
        company_dict['attractiveness_score'] = float(val)
        print(f"  ✓ Set attractiveness_score to {float(val)}")
    else:
        company_dict['attractiveness_score'] = 50.0
        print(f"  ✗ Using default 50.0 (value was None or NaN)")
else:
    company_dict['attractiveness_score'] = 50.0
    print(f"  ✗ Column not found, using default 50.0")

print()
print(f"Final company_dict:")
print(company_dict)
