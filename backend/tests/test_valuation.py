import pytest
from backend.app.services.valuation import ValuationService

# Test 1: Swift in mint condition with normal age and mileage depreciation
def test_valuation_swift_mint():
    res = ValuationService.calculate_fair_value(
        make="Maruti Suzuki",
        model="Swift",
        year=2024,
        reported_odometer=10000,
        fraud_probability=5.0,     # Low fraud risk
        average_wear_score=2.0,    # Low wear
        dents_scratches="None",
        paint_thickness=5.0,       # Normal paint
        asking_price=600000.0      # Asking ₹6,00,000
    )
    
    # Assertions
    assert res["original_msrp"] == 700000.0
    # Swift age = 2026 - 2024 = 2 years. Compounding depreciation: 700,000 * (0.88^2) = 542,080.
    assert res["age_depreciated_value"] == 542080.0
    # Mileage penalty: 10,000 km * 2.5 = 25,000.
    assert res["mileage_penalty"] == 25000.0
    # Base worth: 542,080 - 25,000 = 517,080.
    assert res["base_worth"] == 517080.0
    
    # Fraud penalty: 517,080 * 0.05 * 0.35 = 9,048.90
    assert res["fraud_penalty"] == 9048.90
    # Wear penalty: 517,080 * (2.0/10) * 0.10 = 10,341.60
    assert res["wear_penalty"] == 10341.60
    # Damage penalty: 0
    assert res["damage_penalty"] == 0.0
    # Repaint penalty: 0
    assert res["repaint_penalty"] == 0.0
    assert not res["repaint_detected"]
    
    # Worth: 517,080 - 9,048.90 - 10,341.60 = 497,689.50
    assert res["actual_worth"] == 497689.50
    assert res["asking_price"] == 600000.0
    assert res["price_difference"] == 102310.50 # Overpriced
    assert res["valuation_status"] == "OVERPRICED"

# Test 2: Honda City with Odometer Rollback Scam & structural repaint
def test_valuation_city_scam():
    res = ValuationService.calculate_fair_value(
        make="Honda",
        model="City",
        year=2021,
        reported_odometer=45000,
        fraud_probability=80.0,    # High fraud risk
        average_wear_score=7.5,    # High wear
        dents_scratches="Moderate",# Moderate structural scratches
        paint_thickness=9.2,       # Repaint detected
        asking_price=650000.0      # Asking ₹6,50,000
    )
    
    # Assertions
    assert res["original_msrp"] == 1400000.0
    # City age = 2026 - 2021 = 5 years. Compounding depreciation: 1400000 * (0.88^5) = 738,824.68
    assert res["age_depreciated_value"] == 738824.68
    # Mileage penalty: 45000 * 2.5 = 112500
    assert res["mileage_penalty"] == 112500.0
    # Base worth: 738,824.68 - 112,500 = 626,324.68
    assert res["base_worth"] == 626324.68
    
    # Fraud penalty: 626,324.68 * 0.80 * 0.35 = 175,370.91
    assert res["fraud_penalty"] == 175370.91
    # Wear penalty: 626,324.68 * 0.75 * 0.10 = 46,974.35
    assert res["wear_penalty"] == 46974.35
    # Damage penalty: Moderate dents = 35000
    assert res["damage_penalty"] == 35000.0
    # Repaint penalty: Paint > 7.0 mils = 8% of base worth = 50,105.97
    assert res["repaint_penalty"] == 50105.97
    assert res["repaint_detected"]
    
    # Worth: 626,324.68 - 175,370.91 - 46,974.35 - 35,000 - 50,105.97 = 318,873.45
    assert res["actual_worth"] == 318873.45
    # Since fraud probability is > 60%, the valuation deal status is flagged as SUSPECT SCAM
    assert res["valuation_status"] == "SUSPECT SCAM"
    assert res["price_difference"] == 650000.0 - 318873.45
