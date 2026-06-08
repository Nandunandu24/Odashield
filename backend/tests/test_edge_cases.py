import pytest
from backend.app.services.ecu import EcuService
from backend.app.services.score_aggregator import ScoreAggregatorService

# 1. Test Single-Outlier ECU Replacement (Legitimate swap)
def test_ecu_single_outlier_replacement():
    # ABS is replaced with a low-mileage module (10,000 km)
    # The other 4 modules are tightly grouped around 80,000 km
    readings = {
        "ECM": 80100,
        "TCM": 79900,
        "ABS": 10000,  # Legitimate replacement outlier
        "AIRBAG": 80000,
        "CLUSTER": 80000
    }
    reported_odo = 80000
    engine_hours = 2000.0  # ~40 km/h average speed
    
    res = EcuService.analyze_ecu_consistency(readings, engine_hours, reported_odo)
    
    # Assertions
    assert res["outlier_detected"]
    assert res["outlier_module"] == "ABS"
    assert "legitimate module replacement" in res["outlier_description"].lower()
    
    # The variance used for scoring should ignore ABS and use the variance of the other 4
    # max(80100, 79900, 80000, 80000) - min(80100, 79900, 80000, 80000) = 80100 - 79900 = 200 km
    assert res["variance_km"] == 200
    assert res["ecu_score"] == 0.0  # Verified: Ignored outlier prevents false positive!
    
    # Raw variance remains high
    assert res["raw_variance_km"] == 70100
    
    # Check that in modules list, ABS is marked as REPLACED (OUTLIER) and is not anomalous
    abs_module = next(m for m in res["modules"] if m["module"] == "ABS")
    assert abs_module["status"] == "REPLACED (OUTLIER)"
    assert not abs_module["is_anomalous"]

# 2. Test Dynamic Weight Redistribution (Sparse VAHAN history)
def test_score_aggregator_redistribution():
    # Scenario: High XGBoost (80%) and high Wear (80%), but VAHAN has no history (sufficient_history = False)
    # With VAHAN weight at 30%, a sparse history (Vahan score = 0) would dilute the final score
    # Formula without redistribution (diluted): 80*0.4 (32) + 0*0.3 (0) + 80*0.2 (16) + 0*0.1 (0) = 48.0% (Medium risk)
    # Formula with redistribution (proportionate): 80 * (4/7) + 80 * (2/7) = 80 * (6/7) = 68.57% (High risk)
    
    res = ScoreAggregatorService.aggregate_scores(
        vahan_score=0.0,
        ecu_score=0.0,
        xgboost_score=80.0,
        average_wear_score=8.0, # maps to 80.0 wear score
        reported_odometer=60000,
        sufficient_history=False # Trigger weight redistribution
    )
    
    # Assertions
    assert not res["sufficient_history_flag"]
    assert res["weights_applied"]["vahan"] == 0.0
    assert res["weights_applied"]["xgboost"] == round(4.0/7.0, 3) # 0.571
    assert res["weights_applied"]["wear"] == round(2.0/7.0, 3)    # 0.286
    assert res["weights_applied"]["ecu"] == round(1.0/7.0, 3)     # 0.143
    
    # Expected score check: (80 * 0.571428) + (80 * 0.285714) = 45.714 + 22.857 = 68.57
    assert res["combined_score"] == 68.57
    assert res["risk_level"] == "HIGH"
    assert res["recommendation"] == "REJECT"
