"""Test script to verify score consistency between list and analyze endpoints."""

import os
import sys

# Set environment variables
os.environ['AUTO_TRAIN_ON_IMPORT'] = 'true'
os.environ['KAGGLE_USERNAME'] = 'j8miewong'
os.environ['KAGGLE_KEY'] = 'c9a77ad9e165320072f609c5b0bd704c'

print("Loading model...")
from model import sample_data, analyze_company_comprehensive, ANALYSIS_CACHE

print(f"Loaded {len(sample_data)} companies")

# Test with first company
if len(sample_data) > 0:
    company = sample_data.iloc[0]
    company_id = str(company.get('company_id', ''))
    company_name = str(company.get('company_name', ''))
    
    print(f"\nTesting company: {company_name} (ID: {company_id})")
    
    # Get score from precomputed column (list view)
    list_score = None
    if 'precomputed_attractiveness_score' in company.index:
        list_score = float(company.get('precomputed_attractiveness_score', 0))
        print(f"List view score (precomputed): {list_score:.2f}")
    
    # Prepare data for analysis (modal view)
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
    
    # Check if precomputed values exist in cache
    cached = ANALYSIS_CACHE.get(company_id)
    if cached:
        print(f"Cached analysis found for {company_id}")
        print(f"  Cached score: {cached.get('attractiveness_score', 'N/A')}")
    
    # Call analyze_company_comprehensive (this is what the modal endpoint does)
    print("\nCalling analyze_company_comprehensive...")
    try:
        ml_result = analyze_company_comprehensive(eval_data)
        modal_score = ml_result.get('attractiveness_score', 0)
        print(f"Modal view score (fresh analysis): {modal_score:.2f}")
        
        # Check if the score consistency fix would apply
        if list_score is not None:
            diff = abs(list_score - modal_score)
            print(f"\nScore difference: {diff:.2f}")
            if diff > 0.01:
                print(f"⚠️  INCONSISTENCY DETECTED: List={list_score:.2f}, Modal={modal_score:.2f}")
                print("The fix should override the modal score with the precomputed value.")
            else:
                print("✅ Scores are consistent!")
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

print("\nTest complete!")
