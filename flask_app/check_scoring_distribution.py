#!/usr/bin/env python3
"""
Check the scoring distribution to diagnose if scoring is too lenient
"""
import model
import pandas as pd

def check_distribution():
    """Check the distribution of scores and tiers"""
    df = model.sample_data
    
    if df is None or len(df) == 0:
        print("❌ No sample data loaded")
        return
    
    print(f"📊 Dataset: {len(df)} companies")
    print(f"📊 Data source: {model.data_source}")
    
    if 'precomputed_attractiveness_score' not in df.columns:
        print("\n⚠️  No precomputed scores found. Run precomputation first.")
        return
    
    # Score statistics
    scores = df['precomputed_attractiveness_score'].dropna()
    print(f"\n📈 Score Statistics:")
    print(f"   Count: {len(scores)}")
    print(f"   Mean:  {scores.mean():.2f}")
    print(f"   Std:   {scores.std():.2f}")
    print(f"   Min:   {scores.min():.2f}")
    print(f"   25%:   {scores.quantile(0.25):.2f}")
    print(f"   50%:   {scores.quantile(0.50):.2f}")
    print(f"   75%:   {scores.quantile(0.75):.2f}")
    print(f"   Max:   {scores.max():.2f}")
    
    # Tier distribution
    if 'precomputed_investment_tier_norm' in df.columns:
        tiers = df['precomputed_investment_tier_norm'].value_counts()
        print(f"\n🎯 Tier Distribution:")
        for tier, count in tiers.items():
            pct = (count / len(df)) * 100
            print(f"   {tier:10s}: {count:4d} ({pct:5.1f}%)")
        
        # Check for issues
        avoid_count = tiers.get('avoid', 0)
        invest_pct = (tiers.get('invest', 0) / len(df)) * 100
        
        print(f"\n🔍 Diagnostic:")
        if avoid_count == 0:
            print("   ⚠️  WARNING: No 'avoid' tier companies found!")
            print("   This suggests scoring is too lenient.")
        
        if invest_pct > 80:
            print(f"   ⚠️  WARNING: {invest_pct:.1f}% are 'invest' tier")
            print("   This suggests scoring is too lenient.")
        
        if invest_pct < 20:
            print(f"   ⚠️  WARNING: Only {invest_pct:.1f}% are 'invest' tier")
            print("   This suggests scoring is too strict.")
    
    # Check raw probability distribution
    if 'is_successful' in df.columns:
        success_rate = df['is_successful'].mean()
        print(f"\n🎲 Training Data:")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   (Expected: ~35% for realistic VC outcomes)")

if __name__ == "__main__":
    check_distribution()
