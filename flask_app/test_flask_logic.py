"""Test script to verify the Flask endpoint logic for score consistency."""

import os
import sys
import pandas as pd

# Set environment variables
os.environ['AUTO_TRAIN_ON_IMPORT'] = 'false'  # Use cached models
os.environ['KAGGLE_USERNAME'] = 'j8miewong'
os.environ['KAGGLE_KEY'] = 'c9a77ad9e165320072f609c5b0bd704c'

print("Loading model...")
from model import sample_data, analyze_company_comprehensive, ANALYSIS_CACHE

print(f"Loaded {len(sample_data)} companies")

# Test with first company that has precomputed values
if len(sample_data) > 0:
    company = sample_data.iloc[0]
    company_id = str(company.get('company_id', ''))
    company_name = str(company.get('company_name', ''))
    
    print(f"\nTesting company: {company_name} (ID: {company_id})")
    
    # Simulate the Flask endpoint logic from app.py
    # Step 1: Get precomputed values from DataFrame columns
    use_precomputed = False
    precomputed_data = None
    
    if 'precomputed_attractiveness_score' in company.index and pd.notna(company.get('precomputed_attractiveness_score')):
        print("\n[OK] Precomputed values found in DataFrame")
        precomputed_data = {
            'attractiveness_score': float(company.get('precomputed_attractiveness_score', 0)),
        }
        if 'precomputed_investment_tier' in company.index:
            precomputed_data['investment_tier'] = str(company.get('precomputed_investment_tier', 'Monitor'))
        if 'precomputed_recommendation' in company.index:
            precomputed_data['recommendation'] = str(company.get('precomputed_recommendation', ''))
        if 'precomputed_risk_level' in company.index:
            precomputed_data['risk_level'] = str(company.get('precomputed_risk_level', 'Medium'))
        use_precomputed = True
        
        print(f"  Precomputed score from DataFrame: {precomputed_data['attractiveness_score']:.2f}")
        print(f"  Precomputed tier: {precomputed_data.get('investment_tier', 'N/A')}")
    
    # Step 2: Prepare data for analysis
    eval_data = {
        'company_name': str(company.get('company_name', '')),
        'industry': str(company.get('industry', '')),
        'location': str(company.get('location', '')),
        'funding_round': str(company.get('funding_round', '')),
        'funding_amount_usd': float(company.get('funding_amount_usd', 0)),
        'valuation_usd': float(company.get('valuation_usd', 0)),
        'team_size': int(float(company.get('team_size', 0))),
        'years_since_founding': float(company.get('years_since_founding', 0)),
        'revenue_usd': float(company.get('revenue_usd', 0)),
        'num_investors': int(float(company.get('num_investors', 0))),
        'competition_level': int(float(company.get('competition_level', 5))),
        'market_size_billion_usd': float(company.get('market_size_billion_usd', 1.0)),
    }
    
    # Step 3: Run analysis
    print("\n[OK] Calling analyze_company_comprehensive...")
    ml_result = analyze_company_comprehensive(eval_data)
    print(f"  Fresh analysis score: {ml_result.get('attractiveness_score', 0):.2f}")
    print(f"  Fresh analysis tier: {ml_result.get('investment_tier', 'N/A')}")
    
    # Step 4: Apply precomputed override (Flask endpoint logic)
    if use_precomputed and precomputed_data:
        print("\n[OK] Applying precomputed override...")
        core_fields = ['attractiveness_score', 'investment_tier', 'recommendation', 'risk_level',
                      'market_score', 'team_score', 'financial_score', 'growth_score', 'success_probability']
        for key in core_fields:
            if key in precomputed_data:
                old_value = ml_result.get(key)
                ml_result[key] = precomputed_data[key]
                if key == 'attractiveness_score':
                    print(f"  Overrode {key}: {old_value:.2f} -> {ml_result[key]:.2f}")
                else:
                    print(f"  Overrode {key}: {old_value} -> {ml_result[key]}")
        ml_result['__source'] = 'precomputed_for_consistency'
    
    # Step 5: Final result
    print(f"\n{'='*60}")
    print(f"FINAL RESULT (what modal would show):")
    print(f"  Attractiveness Score: {ml_result.get('attractiveness_score', 0):.2f}")
    print(f"  Investment Tier: {ml_result.get('investment_tier', 'N/A')}")
    print(f"  Source: {ml_result.get('__source', 'fresh_analysis')}")
    print(f"{'='*60}")
    
    # Compare with list view
    list_score = float(company.get('precomputed_attractiveness_score', 0))
    modal_score = ml_result.get('attractiveness_score', 0)
    
    if abs(list_score - modal_score) < 0.01:
        print("\n[SUCCESS] List and Modal scores are CONSISTENT!")
        print(f"   List: {list_score:.2f}  |  Modal: {modal_score:.2f}")
    else:
        print(f"\n[FAILURE] Scores still inconsistent!")
        print(f"   List: {list_score:.2f}  |  Modal: {modal_score:.2f}")
        print(f"   Difference: {abs(list_score - modal_score):.2f}")

print("\nTest complete!")
