#!/usr/bin/env python3
"""
Verify that all thresholds are consistent across Python and JavaScript
"""

print("=" * 80)
print("THRESHOLD CONSISTENCY CHECK")
print("=" * 80)
print()

# Check Python thresholds
print("🐍 Python Backend (model.py):")
print("-" * 80)
try:
    import model
    print(f"✅ TIER_SCORE_BOUNDS['invest']:  {model.TIER_SCORE_BOUNDS['invest']}")
    print(f"✅ TIER_SCORE_BOUNDS['monitor']: {model.TIER_SCORE_BOUNDS['monitor']}")
    print(f"✅ TIER_SCORE_BOUNDS['avoid']:   {model.TIER_SCORE_BOUNDS['avoid']}")
    print()
    print(f"✅ TIER_PROBABILITY_BOUNDS['invest']:  {model.TIER_PROBABILITY_BOUNDS['invest']}")
    print(f"✅ TIER_PROBABILITY_BOUNDS['monitor']: {model.TIER_PROBABILITY_BOUNDS['monitor']}")
    print(f"✅ TIER_PROBABILITY_BOUNDS['avoid']:   {model.TIER_PROBABILITY_BOUNDS['avoid']}")
except Exception as e:
    print(f"❌ Error loading model: {e}")

print()
print("-" * 80)
print()

# Check JavaScript thresholds in HTML
print("🌐 JavaScript Frontend (index.html):")
print("-" * 80)

html_file = "templates/index.html"
try:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count occurrences of old thresholds (should be 0)
    old_60 = content.count('score >= 60') + content.count('>= 60')
    old_45 = content.count('score >= 45') + content.count('>= 45')
    
    # Count occurrences of new thresholds (should be many)
    new_65 = content.count('score >= 65') + content.count('>= 65')
    new_50 = content.count('score >= 50') + content.count('>= 50')
    
    # Check for removed success probability card
    has_probability_card = 'kpi-probability' in content and 'Success Probability' in content
    
    # Check tooltip text
    has_old_tooltip = 'Invest ≥ 60' in content
    has_new_tooltip = 'Invest ≥ 65' in content
    
    print(f"Old thresholds (should be 0):")
    print(f"  score >= 60: {old_60} occurrences {'❌ FOUND OLD!' if old_60 > 0 else '✅'}")
    print(f"  score >= 45: {old_45} occurrences {'❌ FOUND OLD!' if old_45 > 0 else '✅'}")
    print()
    print(f"New thresholds (should be > 0):")
    print(f"  score >= 65: {new_65} occurrences {'✅' if new_65 > 0 else '❌ MISSING!'}")
    print(f"  score >= 50: {new_50} occurrences {'✅' if new_50 > 0 else '❌ MISSING!'}")
    print()
    print(f"Success Probability Card:")
    if has_probability_card:
        print(f"  ⚠️  Warning: 'Success Probability' still appears in HTML")
        print(f"  Check if it's only in comments or if card is still present")
    else:
        print(f"  ✅ Card removed successfully")
    print()
    print(f"Tooltip Text:")
    print(f"  Old tooltip ('Invest ≥ 60'): {'❌ FOUND!' if has_old_tooltip else '✅ Removed'}")
    print(f"  New tooltip ('Invest ≥ 65'): {'✅ Present' if has_new_tooltip else '❌ MISSING!'}")
    
except Exception as e:
    print(f"❌ Error reading HTML file: {e}")

print()
print("-" * 80)
print()

# Test boundary cases
print("🧪 Boundary Case Tests:")
print("-" * 80)

test_scores = [49.9, 50.0, 50.1, 64.9, 65.0, 65.1]

try:
    import model
    for score in test_scores:
        if score >= 65:
            tier = "Invest"
        elif score >= 50:
            tier = "Monitor"
        else:
            tier = "Avoid"
        print(f"  Score {score:5.1f} → {tier:8s} ✅")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)
print()
print("Next steps:")
print("1. If all checks pass: Start server and test in browser")
print("2. Hard refresh browser (Ctrl+Shift+R) to clear cache")
print("3. Check company cards show correct tier badges")
print("4. Open analysis modal - verify no 'Success Probability' card")
print("5. Hover over info icon - verify tooltip shows 'Invest ≥ 65'")
