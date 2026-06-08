import os
import logging
import numpy as np
from typing import Dict, Any, List
from backend.app.config import settings

logger = logging.getLogger(__name__)

# We will import xgboost conditionally to support cases where it might fail or not be present during setup
try:
    import xgboost as xgb
except ImportError:
    xgb = None
    logger.warning("XGBoost library not installed. Falling back to heuristic classifier model.")

class XGBoostService:
    _model = None
    _model_loaded = False
    
    @classmethod
    def load_model(cls) -> bool:
        """
        Loads the trained XGBoost classifier. Returns True if successful.
        """
        if cls._model_loaded:
            return True
            
        model_path = os.path.join(settings.MODEL_DIR, "xgboost_fraud_model.json")
        if not os.path.exists(model_path):
            logger.warning(f"XGBoost model file not found at {model_path}. Will use heuristic fallback.")
            return False
            
        if xgb is None:
            return False
            
        try:
            cls._model = xgb.XGBClassifier()
            cls._model.load_model(model_path)
            cls._model_loaded = True
            logger.info("XGBoost fraud classifier successfully loaded.")
            return True
        except Exception as e:
            logger.error(f"Error loading XGBoost model: {e}")
            return False
            
    @classmethod
    def predict_fraud(
        cls, 
        reported_odometer: int, 
        ecu_readings: Dict[str, int], 
        engine_hours: float
    ) -> Dict[str, Any]:
        """
        Runs fraud prediction on the input parameters.
        """
        # Ensure we have all 5 modules
        required_modules = ["ECM", "TCM", "ABS", "AIRBAG", "CLUSTER"]
        readings = {}
        for module in required_modules:
            readings[module] = ecu_readings.get(module, reported_odometer)
            
        ecu_cluster = readings["CLUSTER"]
        ecu_ecm = readings["ECM"]
        ecu_tcm = readings["TCM"]
        ecu_abs = readings["ABS"]
        ecu_airbag = readings["AIRBAG"]
        
        # Calculate engineered features
        module_readings = [ecu_cluster, ecu_ecm, ecu_tcm, ecu_abs, ecu_airbag]
        max_variance = max(module_readings) - min(module_readings)
        
        avg_speed = 0.0
        if engine_hours > 0:
            avg_speed = reported_odometer / engine_hours
            
        # Try to run model inference
        if cls.load_model() and cls._model is not None:
            try:
                # Prepare features in the exact training order
                # ["reported_odometer", "ecu_ecm", "ecu_tcm", "ecu_abs", "ecu_airbag", "ecu_cluster", "engine_hours", "max_variance", "avg_speed"]
                features_array = np.array([[
                    reported_odometer, ecu_ecm, ecu_tcm, ecu_abs, 
                    ecu_airbag, ecu_cluster, engine_hours, max_variance, 
                    avg_speed
                ]], dtype=np.float32)
                
                # Make prediction
                prob = float(cls._model.predict_proba(features_array)[0][1])
                xgboost_score = round(prob * 100.0, 2)
                
                return {
                    "xgboost_score": xgboost_score,
                    "model_used": "XGBoost Classifier",
                    "features": {
                        "max_variance": max_variance,
                        "avg_speed": round(avg_speed, 2)
                    }
                }
            except Exception as e:
                logger.error(f"Inference error: {e}. Falling back to heuristic classifier.")
                
        # Heuristic fallback if model is missing or fails
        xgboost_score = cls._heuristic_predict(max_variance, avg_speed, reported_odometer)
        return {
            "xgboost_score": xgboost_score,
            "model_used": "Heuristic Classifier (Fallback)",
            "features": {
                "max_variance": max_variance,
                "avg_speed": round(avg_speed, 2)
            }
        }
        
    @staticmethod
    def _heuristic_predict(max_variance: float, avg_speed: float, reported_odometer: int) -> float:
        """
        Mathematical heuristic that approximates the XGBoost model outputs:
        - Odometer variance > 5000 km is a critical indicator (~85% probability)
        - Odometer variance > 1000 km is high indicator (~60% probability)
        - Speed < 15 km/h is highly suspicious (~70% probability)
        """
        score = 5.0  # Base natural fraud rate
        
        if max_variance > 5000:
            score = max(score, 92.0)
        elif max_variance > 1000:
            score = max(score, 65.0)
        elif max_variance > 500:
            score = max(score, 35.0)
            
        if avg_speed > 0:
            if avg_speed < 12.0:
                score = max(score, 88.0)
            elif avg_speed < 18.0:
                score = max(score, 60.0)
            elif avg_speed > 130.0:
                score = max(score, 50.0)
                
        return round(score, 2)
