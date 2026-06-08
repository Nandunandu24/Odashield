from typing import Dict, List, Any
import numpy as np

class EcuService:
    @staticmethod
    def analyze_ecu_consistency(
        ecu_readings: Dict[str, int], 
        engine_hours: float, 
        reported_odometer: int
    ) -> Dict[str, Any]:
        """
        Analyzes consistency across 5 ECU modules: ECM, TCM, ABS, AIRBAG, CLUSTER.
        Parameters:
            ecu_readings: dict containing modules as keys and mileage (int) as values
            engine_hours: engine hours (float)
            reported_odometer: odometer submitted by user (int)
        """
        # Ensure we have all 5 modules. If some are missing, fill them with reported_odometer
        required_modules = ["ECM", "TCM", "ABS", "AIRBAG", "CLUSTER"]
        readings = {}
        for module in required_modules:
            readings[module] = ecu_readings.get(module, reported_odometer)
            
        mileages = list(readings.values())
        
        # Calculate variance metrics
        min_mileage = min(mileages)
        max_mileage = max(mileages)
        raw_variance = max_mileage - min_mileage
        variance = raw_variance
        
        # Single-outlier detection (e.g. replaced ABS/Airbag module)
        outlier_detected = False
        outlier_module = ""
        outlier_description = ""
        
        for module in required_modules:
            other_mileages = [readings[m] for m in required_modules if m != module]
            other_variance = max(other_mileages) - min(other_mileages)
            median_others = float(np.median(other_mileages))
            
            # Legitimate replacement: The replaced module has significantly LOWER mileage
            # If the outlier module has HIGHER mileage, it means the cluster was rolled down (fraud!)
            if other_variance <= 500 and readings[module] < median_others and (median_others - readings[module]) > 2000:
                outlier_detected = True
                outlier_module = module
                outlier_description = (
                    f"Single outlier detected in {module} ({readings[module]:,} km) vs "
                    f"others (~{int(median_others):,} km). Indication of legitimate module replacement."
                )
                variance = other_variance
                break
        
        # Calculate ECU Score (0-100)
        if variance <= 500:
            ecu_score = 0.0
        elif variance >= 5000:
            ecu_score = 100.0
        else:
            ecu_score = round(((variance - 500) / 4500) * 100.0, 2)
            
        # Analyze engine hours speed consistency
        # average speed = odometer / engine_hours
        avg_speed = 0.0
        engine_hours_anomaly = False
        hours_description = ""
        
        if engine_hours > 0:
            avg_speed = round(reported_odometer / engine_hours, 2)
            # Normal city/highway average speed is 20 to 80 km/h
            if avg_speed < 15.0:
                engine_hours_anomaly = True
                hours_description = f"Reported average speed is extremely low ({avg_speed} km/h). This indicates the odometer was rolled back but engine hours remained unchanged."
                # Boost ECU score if speed is suspiciously low
                ecu_score = max(ecu_score, 80.0)
            elif avg_speed > 120.0:
                engine_hours_anomaly = True
                hours_description = f"Reported average speed is physically improbable ({avg_speed} km/h). This indicates engine hours counter may have been reset or tampered."
                ecu_score = max(ecu_score, 50.0)
                
        # Format modules breakdown for the frontend
        modules_breakdown = []
        for name, value in readings.items():
            diff = value - reported_odometer
            is_anom = abs(diff) > 500
            status_str = "ALIGNED"
            
            if name == outlier_module:
                is_anom = False  # Filtered outlier is not a fraud anomaly
                status_str = "REPLACED (OUTLIER)"
            elif is_anom:
                status_str = "DISCREPANCY"
                
            modules_breakdown.append({
                "module": name,
                "mileage": value,
                "difference": diff,
                "is_anomalous": is_anom,
                "status": status_str
            })
            
        return {
            "ecu_score": ecu_score,
            "variance_km": variance,
            "raw_variance_km": raw_variance,
            "engine_hours": engine_hours,
            "avg_speed_kmh": avg_speed,
            "engine_hours_anomaly": engine_hours_anomaly,
            "hours_description": hours_description,
            "modules": modules_breakdown,
            "has_variance_anomaly": variance > 500,
            "outlier_detected": outlier_detected,
            "outlier_module": outlier_module,
            "outlier_description": outlier_description
        }
