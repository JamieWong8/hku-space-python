#!/usr/bin/env python3
"""
Test script to verify the modernized analysis pipeline works correctly
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Testing modernized analysis pipeline...")

try:
    # Test importing the new function
    from model import analyze_company_comprehensive, sample_data
    print("✅ Successfully imported analyze_company_comprehensive")
    
    # Check if sample data is available
    if sample_data is not None:
        print(f"✅ Sample data loaded: {len(sample_data)} companies")
        
        # Get a real company from the data for testing
        test_company = sample_data.iloc[0]
        print(f"📊 Testing with: {test_company['company_name']}")
        
        # Prepare evaluation data the same way the Flask app does
        eval_data = {
            'company_name': str(test_company['company_name']),
            'industry': str(test_company.get('industry', 'SaaS')),
            'location': str(test_company.get('location', 'San Francisco')),
            'funding_round': str(test_company.get('funding_round', 'Series A')),
            'funding_amount_usd': float(test_company.get('funding_amount_usd', 0)) if pd.notna(test_company.get('funding_amount_usd')) else 0.0,
            'valuation_usd': float(test_company.get('valuation_usd', 0)) if pd.notna(test_company.get('valuation_usd')) else 0.0,
            'team_size': int(float(test_company.get('team_size', 0))) if pd.notna(test_company.get('team_size')) else 10,
            'years_since_founding': float(test_company.get('years_since_founding', 0)) if pd.notna(test_company.get('years_since_founding')) else 0.0,
            'revenue_usd': float(test_company.get('revenue_usd', 0)) if pd.notna(test_company.get('revenue_usd')) else 0.0,
            'num_investors': int(float(test_company.get('num_investors', 0))) if pd.notna(test_company.get('num_investors')) else 0,
            'competition_level': int(float(test_company.get('competition_level', 0))) if pd.notna(test_company.get('competition_level')) else 5,
            'market_size_billion_usd': float(test_company.get('market_size_billion_usd', 0)) if pd.notna(test_company.get('market_size_billion_usd')) else 1.0,
        }
        
        # Test the new comprehensive analysis function
        print("\n🧪 Running comprehensive analysis...")
        result = analyze_company_comprehensive(eval_data)
        
        print("\n✅ Analysis complete! Results:")
        print(f"📈 Attractiveness Score: {result['attractiveness_score']:.1f}%")
        print(f"🎯 Success Probability: {result['success_probability']:.1%}")
        print(f"💰 Predicted Funding: ${result['predicted_funding']:,.0f}")
        print(f"⭐ Recommendation: {result['recommendation']}")
        print(f"🏆 Investment Tier: {result['investment_tier']}")
        print(f"⚠️ Risk Level: {result['risk_level']}")
        
        print(f"\n📋 Component Scores:")
        print(f"   🎯 Market Score: {result['market_score']:.1f}/100")
        print(f"   👥 Team Score: {result['team_score']:.1f}/100")
        print(f"   💵 Financial Score: {result['financial_score']:.1f}/100")
        print(f"   📈 Growth Score: {result['growth_score']:.1f}/100")
        
        print(f"\n💬 Investment Commentary ({len(result['investment_commentary'])} points):")
        for i, comment in enumerate(result['investment_commentary'][:5]):  # Show first 5 comments
            print(f"   {i+1}. {comment}")
        
        print(f"\n🔍 Key Insights ({len(result['insights'])} points):")
        for i, insight in enumerate(result['insights'][:3]):  # Show first 3 insights
            print(f"   {i+1}. {insight}")
            
        print("\n✅ Investment commentary successfully integrated!")
        print("✅ All expected fields present in result")
        
    else:
        print("❌ Sample data not available")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Pipeline test complete!")