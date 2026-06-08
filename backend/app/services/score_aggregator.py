from typing import Dict, Any

class ScoreAggregatorService:
    @staticmethod
    def aggregate_scores(
        vahan_score: float,
        ecu_score: float,
        xgboost_score: float,
        average_wear_score: float,
        reported_odometer: int,
        sufficient_history: bool = True
    ) -> Dict[str, Any]:
        """
        Combines layer scores and calculates the final fraud probability.
        Formula: XGBoost (40%) + VAHAN (30%) + Wear (20%) + ECU (10%)
        
        If there is insufficient history, VAHAN's 30% weight is redistributed proportionally:
        - XGBoost: 40% -> 57.14% (4/7)
        - Wear: 20% -> 28.57% (2/7)
        - ECU: 10% -> 14.29% (1/7)
        """
        # Layer 4 Physical Wear: Maps average_wear_score (0-10) to 0-100 scale.
        # Anomalies check: if wear score is high but odometer is low, it triggers a fraud signal override
        is_wear_mismatch = False
        wear_description = ""
        
        # Base wear score calculation
        wear_fraud_score = average_wear_score * 10.0
        
        if average_wear_score > 6.0 and reported_odometer < 50000:
            is_wear_mismatch = True
            wear_fraud_score = 100.0  # Set to max wear fraud score because of mismatch
            wear_description = f"Physical wear score is high ({average_wear_score}/10) despite extremely low reported odometer ({reported_odometer:,} km). This is a strong indicator of cosmetic refurbishment to mask mileage."
        else:
            wear_description = f"Physical wear score of {average_wear_score}/10 is consistent with the reported odometer reading."

        # Define default weights
        w_xgb = 0.40
        w_vahan = 0.30
        w_wear = 0.20
        w_ecu = 0.10
        
        if not sufficient_history:
            # Redistribute weights proportionally to remaining active layers (sum to 0.70)
            w_xgb = 4.0 / 7.0
            w_wear = 2.0 / 7.0
            w_ecu = 1.0 / 7.0
            w_vahan = 0.0

        # Apply aggregation weights
        combined_score = (
            (xgboost_score * w_xgb) +
            (vahan_score * w_vahan) +
            (wear_fraud_score * w_wear) +
            (ecu_score * w_ecu)
        )
        
        final_probability = round(min(100.0, max(0.0, combined_score)), 2)
        
        # Risk level and recommendation classification
        if final_probability < 30.0:
            risk_level = "LOW"
            recommendation = "ACCEPT"
        elif final_probability < 60.0:
            risk_level = "MEDIUM"
            recommendation = "REVIEW"
        elif final_probability < 85.0:
            risk_level = "HIGH"
            recommendation = "REJECT"
        else:
            risk_level = "CRITICAL"
            recommendation = "REJECT"
            
        return {
            "vahan_score": vahan_score,
            "ecu_score": ecu_score,
            "xgboost_score": xgboost_score,
            "wear_score": wear_fraud_score,
            "combined_score": final_probability,
            "fraud_probability": final_probability,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "wear_mismatch": {
                "is_detected": is_wear_mismatch,
                "description": wear_description
            },
            "weights_applied": {
                "vahan": round(w_vahan, 3),
                "xgboost": round(w_xgb, 3),
                "wear": round(w_wear, 3),
                "ecu": round(w_ecu, 3)
            },
            "sufficient_history_flag": sufficient_history
        }
