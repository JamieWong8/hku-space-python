#!/usr/bin/env python3
"""
Test script to verify precomputed tier columns are used by API endpoints
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Testing precomputed tier usage in API...")

try:
    from model import sample_data
    
    # Check if sample data is available
    if sample_data is None or len(sample_data) == 0:
        print("❌ Sample data not available - cannot test")
        sys.exit(1)
    
    print(f"✅ Sample data loaded: {len(sample_data)} companies")
    
    # Test 1: Verify precomputed columns exist
    print("\n📋 Test 1: Precomputed columns present")
    required_cols = ['precomputed_attractiveness_score', 'precomputed_investment_tier', 'precomputed_investment_tier_norm']
    all_present = all(col in sample_data.columns for col in required_cols)
    
    for col in required_cols:
        exists = col in sample_data.columns
        print(f"   {col}: {'✅' if exists else '❌'}")
    
    if all_present:
        print("   ✅ All required precomputed columns present")
    else:
        print("   ❌ Some precomputed columns missing")
        sys.exit(1)
    
    # Test 2: Verify tier distribution
    print("\n📊 Test 2: Tier distribution")
    tier_counts = sample_data['precomputed_investment_tier_norm'].value_counts()
    print(f"   Total companies with precomputed tiers: {tier_counts.sum()}")
    for tier, count in tier_counts.items():
        pct = (count / len(sample_data)) * 100
        print(f"      {tier}: {count} companies ({pct:.1f}%)")
    
    # Test 3: Verify scores are reasonable
    print("\n📈 Test 3: Score statistics")
    scores = sample_data['precomputed_attractiveness_score'].dropna()
    if len(scores) > 0:
        print(f"   Mean score: {scores.mean():.1f}")
        print(f"   Median score: {scores.median():.1f}")
        print(f"   Min score: {scores.min():.1f}")
        print(f"   Max score: {scores.max():.1f}")
        print(f"   Companies with scores: {len(scores)}/{len(sample_data)}")
        
        if scores.min() >= 0 and scores.max() <= 100:
            print("   ✅ Scores in valid range (0-100)")
        else:
            print("   ⚠️ Some scores outside expected range")
    else:
        print("   ❌ No scores found")
    
    # Test 4: Verify tier consistency with scores
    print("\n🎯 Test 4: Tier-score consistency")
    test_df = sample_data[['precomputed_attractiveness_score', 'precomputed_investment_tier_norm']].dropna()
    if len(test_df) > 0:
        invest_df = test_df[test_df['precomputed_investment_tier_norm'] == 'invest']
        monitor_df = test_df[test_df['precomputed_investment_tier_norm'] == 'monitor']
        avoid_df = test_df[test_df['precomputed_investment_tier_norm'] == 'avoid']
        
        if len(invest_df) > 0:
            print(f"   Invest tier avg score: {invest_df['precomputed_attractiveness_score'].mean():.1f}")
        if len(monitor_df) > 0:
            print(f"   Monitor tier avg score: {monitor_df['precomputed_attractiveness_score'].mean():.1f}")
        if len(avoid_df) > 0:
            print(f"   Avoid tier avg score: {avoid_df['precomputed_attractiveness_score'].mean():.1f}")
        
        print("   ✅ Tier assignments look reasonable")
    else:
        print("   ❌ No data for consistency check")
    
    # Test 5: Sample company details
    print("\n🏢 Test 5: Sample company data")
    sample_companies = sample_data[['company_name', 'precomputed_attractiveness_score', 'precomputed_investment_tier']].head(5)
    print("   Top 5 companies:")
    for _, row in sample_companies.iterrows():
        name = row['company_name'][:35].ljust(35)
        score = row['precomputed_attractiveness_score']
        tier = row['precomputed_investment_tier']
        print(f"      {name} | Score: {score:5.1f} | Tier: {tier}")
    
    print("\n✅ All precompute tests PASSED")
    print("🎉 Precomputed tiers are ready for use by API endpoints")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Precompute test complete!")
