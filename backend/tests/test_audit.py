import pytest
from datetime import date
from backend.app.database import VahanRecord
from backend.app.services.vahan import VahanService
from backend.app.services.ecu import EcuService
from backend.app.services.xgboost_model import XGBoostService
from backend.app.services.score_aggregator import ScoreAggregatorService

# Mock records helper
def create_mock_vahan_record(odometer: int, days_offset: int, owner_number: int) -> VahanRecord:
    return VahanRecord(
        recorded_date=date(2020, 1, 1), # placeholder
        odometer_reading=odometer,
        owner_number=owner_number
    )

# 1. Test Layer 1 (VAHAN Cross-Reference)
def test_vahan_service_clean_timeline():
    # Ordered odometer growth
    records = [
        create_mock_vahan_record(12000, 100, 1),
        create_mock_vahan_record(25000, 200, 1),
        create_mock_vahan_record(38000, 300, 2)
    ]
    res = VahanService.analyze_timeline(records, 45000)
    
    assert res["vahan_score"] == 0.0
    assert not res["has_rollback"]
    assert len(res["anomalies"]) == 0

def test_vahan_service_historical_rollback():
    # Historical drop: 38000 -> 25000
    records = [
        create_mock_vahan_record(12000, 100, 1),
        create_mock_vahan_record(38000, 200, 1),
        create_mock_vahan_record(25000, 300, 2)
    ]
    res = VahanService.analyze_timeline(records, 45000)
    
    assert res["vahan_score"] == 100.0
    assert res["has_rollback"]
    assert len(res["anomalies"]) >= 1
    assert "dropped from 38,000" in res["anomalies"][0]["description"]

def test_vahan_service_current_discrepancy():
    # Reported reading (40000) lower than last historical (48000)
    records = [
        create_mock_vahan_record(12000, 100, 1),
        create_mock_vahan_record(30000, 200, 1),
        create_mock_vahan_record(48000, 300, 2)
    ]
    res = VahanService.analyze_timeline(records, 40000)
    
    assert res["vahan_score"] == 100.0
    assert res["has_rollback"]
    assert len(res["anomalies"]) >= 1
    assert any("Reported odometer" in a["description"] for a in res["anomalies"])


# 2. Test Layer 2 (ECU Consistency)
def test_ecu_service_aligned():
    readings = {"ECM": 40000, "TCM": 40100, "ABS": 39900, "AIRBAG": 40000, "CLUSTER": 40000}
    res = EcuService.analyze_ecu_consistency(readings, 1000.0, 40000)
    
    assert res["ecu_score"] == 0.0
    assert res["variance_km"] == 200
    assert not res["has_variance_anomaly"]
    assert not res["engine_hours_anomaly"]

def test_ecu_service_anomalous_variance():
    # High variance: ECM has 62000 km, reported is 40000
    readings = {"ECM": 62000, "TCM": 40100, "ABS": 40000, "AIRBAG": 40000, "CLUSTER": 40000}
    res = EcuService.analyze_ecu_consistency(readings, 1000.0, 40000)
    
    assert res["variance_km"] == 22000
    assert res["ecu_score"] == 100.0
    assert res["has_variance_anomaly"]

def test_ecu_service_engine_hours_anomaly():
    # Reported odo 20000 km with 2000 engine hours = 10 km/h average speed (suspiciously low)
    readings = {"ECM": 20000, "TCM": 20000, "ABS": 20000, "AIRBAG": 20000, "CLUSTER": 20000}
    res = EcuService.analyze_ecu_consistency(readings, 2000.0, 20000)
    
    assert res["engine_hours_anomaly"]
    assert "average speed is extremely low" in res["hours_description"]
    assert res["ecu_score"] >= 80.0


# 3. Test Layer 3 (XGBoost Classifier Inference)
def test_xgboost_service_heuristic_predict():
    # High variance -> high probability
    res_high = XGBoostService.predict_fraud(30000, {"ECM": 75000, "CLUSTER": 30000}, 2000.0)
    assert res_high["xgboost_score"] >= 80.0
    
    # Clean, low variance, regular hours -> low probability
    res_clean = XGBoostService.predict_fraud(40000, {"ECM": 40100, "CLUSTER": 40000}, 1000.0)
    assert res_clean["xgboost_score"] <= 10.0


# 4. Test Layer 6 (Aggregation)
def test_aggregator_score_math():
    # Formula: XGBoost (40%) + VAHAN (30%) + Wear (20%) + ECU (10%)
    # Input: Vahan=0, ECU=0, XGB=10, Wear=2.0 (equivalent to 20%), Reported=60000
    res = ScoreAggregatorService.aggregate_scores(
        vahan_score=0.0,
        ecu_score=0.0,
        xgboost_score=10.0,
        average_wear_score=2.0,
        reported_odometer=60000
    )
    
    # 10*0.4 + 20*0.2 = 4 + 4 = 8.0
    assert res["combined_score"] == 8.0
    assert res["risk_level"] == "LOW"
    assert res["recommendation"] == "ACCEPT"

def test_aggregator_wear_mismatch():
    # Odo < 50K but average wear > 6.0
    res = ScoreAggregatorService.aggregate_scores(
        vahan_score=0.0,
        ecu_score=0.0,
        xgboost_score=0.0,
        average_wear_score=8.0,
        reported_odometer=30000
    )
    
    # Trigger mismatch override: wear_fraud_score = 100.0
    # Combined score = 100.0 * 0.20 = 20.0
    assert res["wear_mismatch"]["is_detected"]
    assert res["combined_score"] == 20.0
