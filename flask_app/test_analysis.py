#!/usr/bin/env python3
"""
Quick test of the new analyze_company_comprehensive function
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model import analyze_company_comprehensive

# Test company data
test_company = {
    'company_name': 'TestCorp Inc',
    'industry': 'SaaS',
    'location': 'San Francisco',
    'funding_round': 'Series A',
    'funding_amount_usd': 5000000,
    'valuation_usd': 25000000,
    'team_size': 15,
    'years_since_founding': 2.5,
    'revenue_usd': 500000,
    'num_investors': 3,
    'competition_level': 5,
    'market_size_billion_usd': 10.0,
}

print("🧪 Testing analyze_company_comprehensive function...")
print(f"📊 Test Company: {test_company['company_name']}")

try:
    result = analyze_company_comprehensive(test_company)
    print("\n✅ Function executed successfully!")
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
    
    print(f"\n💬 Investment Commentary:")
    for comment in result['investment_commentary'][:3]:  # Show first 3 comments
        print(f"   • {comment}")
    
    print(f"\n🔍 Key Insights:")
    for insight in result['insights'][:3]:  # Show first 3 insights
        print(f"   • {insight}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Test complete!")