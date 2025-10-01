#!/usr/bin/env python3
"""Test scores around the 65.0 boundary"""
import model
import pandas as pd

df = model.sample_data
if 'precomputed_attractiveness_score' in df.columns:
    scores = df['precomputed_attractiveness_score']
    tiers = df['precomputed_investment_tier']
    
    # Check scores around 65.0 boundary
    boundary = df[(scores >= 64.5) & (scores <= 65.5)]
    
    print("Scores around 65.0 boundary:")
    print("-" * 80)
    for idx, row in boundary.iterrows():
        score = row['precomputed_attractiveness_score']
        tier = row['precomputed_investment_tier']
        name = row['company_name']
        print(f"{name[:30]:30s} Score: {score:6.2f}  Tier: {tier}")
    
    print("\n" + "=" * 80)
    print("Checking exact 65.0 scores:")
    exact_65 = df[abs(scores - 65.0) < 0.01]
    print(f"Count: {len(exact_65)}")
    if len(exact_65) > 0:
        print(exact_65[['company_name', 'precomputed_attractiveness_score', 'precomputed_investment_tier']].head(5))
else:
    print("No precomputed data found")
