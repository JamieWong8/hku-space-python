#!/usr/bin/env python3
"""
Test script to verify automatic tier precomputation after training
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Testing automatic tier precomputation...")

try:
    from model import sample_data, train_models, _fast_bootstrap_models
    
    # Check if sample data is available
    if sample_data is None or len(sample_data) == 0:
        print("❌ Sample data not available - cannot test")
        sys.exit(1)
    
    print(f"✅ Sample data loaded: {len(sample_data)} companies")
    
    # Test 1: Verify precomputed columns don't exist yet (fresh state)
    print("\n📋 Test 1: Initial state check")
    has_precomputed = 'precomputed_attractiveness_score' in sample_data.columns
    print(f"   Precomputed columns present: {has_precomputed}")
    
    # Test 2: Run bootstrap training (fast)
    print("\n🏃 Test 2: Running bootstrap training...")
    print("   This should automatically precompute tiers after training")
    result = _fast_bootstrap_models(n_samples=100)
    
    if result:
        print(f"   ✅ Bootstrap training completed")
        print(f"   Data source: {result.get('data_source', 'unknown')}")
        print(f"   Rows used: {result.get('rows', 0)}")
        
        # Verify precomputed columns were created
        from model import sample_data as updated_data
        has_score = 'precomputed_attractiveness_score' in updated_data.columns
        has_tier = 'precomputed_investment_tier' in updated_data.columns
        has_tier_norm = 'precomputed_investment_tier_norm' in updated_data.columns
        
        print(f"\n   Precomputed columns created:")
        print(f"      attractiveness_score: {has_score}")
        print(f"      investment_tier: {has_tier}")
        print(f"      investment_tier_norm: {has_tier_norm}")
        
        if has_score and has_tier and has_tier_norm:
            print("   ✅ All precomputed columns created successfully")
            
            # Show tier distribution
            if has_tier_norm:
                tier_counts = updated_data['precomputed_investment_tier_norm'].value_counts()
                print(f"\n   📊 Tier distribution:")
                for tier, count in tier_counts.items():
                    print(f"      {tier}: {count} companies")
            
            # Sample a few scores
            sample_scores = updated_data[['company_name', 'precomputed_attractiveness_score', 'precomputed_investment_tier']].head(5)
            print(f"\n   📈 Sample precomputed scores:")
            for _, row in sample_scores.iterrows():
                print(f"      {row['company_name'][:30]:30s} - Score: {row['precomputed_attractiveness_score']:5.1f} - Tier: {row['precomputed_investment_tier']}")
            
            print("\n✅ Auto-precompute test PASSED")
        else:
            print("   ❌ Some precomputed columns missing")
    else:
        print("   ❌ Bootstrap training failed")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Auto-precompute test complete!")
