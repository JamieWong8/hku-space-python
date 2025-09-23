"""Test that our new analysis function works and includes investment commentary"""

# Simple test data
test_data = {
    'company_name': 'TestStartup Inc',
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

try:
    from model import analyze_company_comprehensive
    print("✅ Import successful")
    
    result = analyze_company_comprehensive(test_data)
    print("✅ Function execution successful")
    
    # Check required fields
    required_fields = ['company_name', 'attractiveness_score', 'success_probability', 
                      'predicted_funding', 'recommendation', 'insights', 
                      'investment_commentary', 'risk_level', 'investment_tier']
    
    missing_fields = [field for field in required_fields if field not in result]
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
    else:
        print("✅ All required fields present")
    
    # Validate investment commentary
    if 'investment_commentary' in result and len(result['investment_commentary']) > 0:
        print(f"✅ Investment commentary generated: {len(result['investment_commentary'])} points")
        print(f"   Sample: {result['investment_commentary'][0]}")
    else:
        print("❌ No investment commentary generated")
    
    print(f"📊 Analysis Score: {result.get('attractiveness_score', 0):.1f}%")
    print(f"⭐ Recommendation: {result.get('recommendation', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()