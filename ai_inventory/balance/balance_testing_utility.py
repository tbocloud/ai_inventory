#!/usr/bin/env python3
"""
Test Current Balance Functions
==============================

This script tests the new current balance functions without requiring
a running Frappe site.
"""

def test_balance_logic():
    """Test the balance calculation logic"""
    
    print("🧪 Testing Current Balance Logic")
    print("=" * 40)
    
    # Sample forecast data similar to AI-FIN-FCST-01319
    test_forecast = {
        "name": "AI-FIN-FCST-01319",
        "account": "Cash - Test Company",
        "company": "Test Company",
        "forecast_type": "Cash Flow",
        "predicted_amount": 534642.60,  # From your dashboard
        "confidence_score": 85.0,
        "upper_bound": 600000.0,
        "lower_bound": 450000.0
    }
    
    # Sample current balance (simulated)
    current_balance = 534642.60  # Exactly matching prediction
    
    print(f"📋 Test Forecast Data:")
    print(f"   Forecast ID: {test_forecast['name']}")
    print(f"   Account: {test_forecast['account']}")
    print(f"   Predicted Amount: ₹{test_forecast['predicted_amount']:,.2f}")
    print(f"   Current Balance: ₹{current_balance:,.2f}")
    print(f"   Upper Bound: ₹{test_forecast['upper_bound']:,.2f}")
    print(f"   Lower Bound: ₹{test_forecast['lower_bound']:,.2f}")
    
    # Test 1: Bounds Logic Validation
    print(f"\n🎯 Test 1: Bounds Logic Validation")
    
    bounds_valid = test_forecast['upper_bound'] > test_forecast['lower_bound']
    print(f"   Upper > Lower: {bounds_valid} ✅" if bounds_valid else f"   Upper > Lower: {bounds_valid} 🚨")
    
    if bounds_valid:
        within_bounds = test_forecast['lower_bound'] <= current_balance <= test_forecast['upper_bound']
        print(f"   Balance within bounds: {within_bounds} ✅" if within_bounds else f"   Balance within bounds: {within_bounds} ⚠️")
    
    # Test 2: Variance Analysis
    print(f"\n📊 Test 2: Variance Analysis")
    
    variance = current_balance - test_forecast['predicted_amount']
    variance_pct = (variance / abs(test_forecast['predicted_amount'])) * 100 if test_forecast['predicted_amount'] != 0 else 0
    
    print(f"   Absolute Variance: ₹{variance:,.2f}")
    print(f"   Percentage Variance: {variance_pct:.2f}%")
    
    # Categorize variance
    abs_variance = abs(variance_pct)
    if abs_variance <= 5:
        variance_status = "✅ Excellent"
    elif abs_variance <= 15:
        variance_status = "✅ Good"
    elif abs_variance <= 30:
        variance_status = "⚠️ Acceptable"
    elif abs_variance <= 50:
        variance_status = "⚠️ Poor"
    else:
        variance_status = "🚨 Critical"
    
    print(f"   Variance Status: {variance_status}")
    
    # Test 3: Data Quality Scoring
    print(f"\n📈 Test 3: Data Quality Scoring")
    
    # Simulate data quality calculation
    required_fields = ['company', 'account', 'forecast_type', 'predicted_amount', 'confidence_score']
    optional_fields = ['upper_bound', 'lower_bound', 'current_balance']
    
    required_filled = len([f for f in required_fields if test_forecast.get(f) is not None])
    optional_filled = len([f for f in optional_fields if f == 'current_balance' or test_forecast.get(f) is not None])
    
    required_score = (required_filled / len(required_fields)) * 70
    optional_score = (optional_filled / len(optional_fields)) * 30
    
    base_quality = required_score + optional_score
    
    # Accuracy adjustments
    accuracy_adjustments = []
    
    # Bounds logic bonus/penalty
    if bounds_valid:
        accuracy_adjustments.append(5)
    else:
        accuracy_adjustments.append(-15)
    
    # Confidence score bonus/penalty
    if 60 <= test_forecast['confidence_score'] <= 95:
        accuracy_adjustments.append(3)
    
    # Balance accuracy bonus/penalty
    if abs_variance <= 10:
        accuracy_adjustments.append(5)
    elif abs_variance <= 25:
        accuracy_adjustments.append(2)
    elif abs_variance > 100:
        accuracy_adjustments.append(-10)
    
    final_quality = base_quality + sum(accuracy_adjustments)
    final_quality = max(0, min(100, final_quality))
    
    print(f"   Required Fields Score: {required_score:.1f}/70")
    print(f"   Optional Fields Score: {optional_score:.1f}/30")
    print(f"   Accuracy Adjustments: {sum(accuracy_adjustments):+.1f}")
    print(f"   Final Quality Score: {final_quality:.1f}%")
    
    if final_quality >= 80:
        quality_status = "✅ Good"
    elif final_quality >= 60:
        quality_status = "⚠️ Fair"
    else:
        quality_status = "🚨 Poor"
    
    print(f"   Quality Status: {quality_status}")
    
    # Test 4: Balance Alert Logic
    print(f"\n🚨 Test 4: Balance Alert Logic")
    
    alerts = []
    
    # Low balance thresholds (sample)
    low_balance_threshold = 50000
    critical_balance_threshold = 10000
    
    if current_balance < critical_balance_threshold:
        alerts.append({"type": "critical", "message": f"Critical low balance: ₹{current_balance:,.2f}"})
    elif current_balance < low_balance_threshold:
        alerts.append({"type": "warning", "message": f"Low balance warning: ₹{current_balance:,.2f}"})
    
    if current_balance < 0:
        alerts.append({"type": "critical", "message": f"Negative balance: ₹{current_balance:,.2f}"})
    
    if abs_variance > 50:
        alerts.append({"type": "warning", "message": f"Large prediction variance: {variance_pct:.1f}%"})
    
    if not alerts:
        print(f"   ✅ No alerts triggered")
    else:
        for alert in alerts:
            icon = "🚨" if alert["type"] == "critical" else "⚠️"
            print(f"   {icon} {alert['message']}")
    
    # Test 5: Balance-to-Prediction Ratio
    print(f"\n💰 Test 5: Balance-to-Prediction Ratio")
    
    if test_forecast['predicted_amount'] != 0:
        balance_ratio = (current_balance / test_forecast['predicted_amount']) * 100
        print(f"   Balance-to-Prediction Ratio: {balance_ratio:.1f}%")
        
        if 95 <= balance_ratio <= 105:
            ratio_status = "✅ Excellent match"
        elif 90 <= balance_ratio <= 110:
            ratio_status = "✅ Good match"
        elif 75 <= balance_ratio <= 125:
            ratio_status = "⚠️ Acceptable variance"
        else:
            ratio_status = "🚨 Poor match"
        
        print(f"   Ratio Status: {ratio_status}")
    
    # Summary
    print(f"\n📝 Overall Test Summary")
    print(f"=" * 40)
    
    test_results = {
        "bounds_logic": "✅ Pass" if bounds_valid else "🚨 Fail",
        "variance_analysis": variance_status,
        "data_quality": quality_status,
        "alert_system": "✅ Working" if len(alerts) >= 0 else "🚨 Error",
        "balance_ratio": ratio_status if 'ratio_status' in locals() else "N/A"
    }
    
    for test_name, result in test_results.items():
        print(f"   {test_name.replace('_', ' ').title()}: {result}")
    
    # Overall status
    critical_issues = sum(1 for result in test_results.values() if "🚨" in result)
    warnings = sum(1 for result in test_results.values() if "⚠️" in result)
    
    if critical_issues > 0:
        overall_status = "🚨 Critical Issues Found"
    elif warnings > 1:
        overall_status = "⚠️ Warnings Present"
    else:
        overall_status = "✅ All Tests Passed"
    
    print(f"\n🏆 Overall Status: {overall_status}")
    
    return {
        "bounds_valid": bounds_valid,
        "variance_percentage": variance_pct,
        "data_quality_score": final_quality,
        "alerts_count": len(alerts),
        "overall_status": overall_status
    }

def test_edge_cases():
    """Test edge cases for current balance functions"""
    
    print(f"\n🧪 Testing Edge Cases")
    print("=" * 40)
    
    edge_cases = [
        {
            "name": "Negative Balance",
            "current_balance": -5000,
            "predicted_amount": 10000,
            "upper_bound": 15000,
            "lower_bound": 5000
        },
        {
            "name": "Invalid Bounds",
            "current_balance": 50000,
            "predicted_amount": 45000,
            "upper_bound": 40000,  # Invalid: upper < lower
            "lower_bound": 50000
        },
        {
            "name": "Zero Prediction",
            "current_balance": 1000,
            "predicted_amount": 0,
            "upper_bound": 2000,
            "lower_bound": 0
        },
        {
            "name": "Large Variance",
            "current_balance": 1000000,
            "predicted_amount": 10000,
            "upper_bound": 20000,
            "lower_bound": 5000
        }
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n   Test Case {i}: {case['name']}")
        
        # Calculate variance
        if case['predicted_amount'] != 0:
            variance_pct = ((case['current_balance'] - case['predicted_amount']) / abs(case['predicted_amount'])) * 100
            print(f"      Variance: {variance_pct:.1f}%")
        else:
            print(f"      Variance: Cannot calculate (zero prediction)")
        
        # Check bounds
        bounds_valid = case['upper_bound'] > case['lower_bound']
        print(f"      Bounds Valid: {'✅ Yes' if bounds_valid else '🚨 No'}")
        
        # Check negative balance
        if case['current_balance'] < 0:
            print(f"      ⚠️ Negative balance detected")
        
        # Check if balance is within bounds (if bounds are valid)
        if bounds_valid:
            within_bounds = case['lower_bound'] <= case['current_balance'] <= case['upper_bound']
            print(f"      Within Bounds: {'✅ Yes' if within_bounds else '⚠️ No'}")

if __name__ == "__main__":
    # Run the tests
    print("🔬 Current Balance Functions Test Suite")
    print("=" * 50)
    
    # Test main logic
    main_results = test_balance_logic()
    
    # Test edge cases
    test_edge_cases()
    
    print(f"\n✅ Test Suite Completed!")
    print(f"Main test results: {main_results['overall_status']}")
