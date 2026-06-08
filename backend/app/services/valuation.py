import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ValuationService:
    @staticmethod
    def calculate_fair_value(
        make: str,
        model: str,
        year: int,
        reported_odometer: int,
        fraud_probability: float,
        average_wear_score: float,
        dents_scratches: str = "None",
        paint_thickness: float = 5.0,
        asking_price: Optional[float] = None,
        insurance_claims_total_amount: float = 0.0,
        insurance_is_expired: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates the estimated fair market value of a used car in INR (₹).
        Applies penalties for age, odometer mileage, odometer fraud risk probability,
        CNN visual wear indicators, repainting, and structural damage (dents/scratches).
        """
        # 1. Resolve Original MSRP (New Price) based on mock vehicle list
        make_lower = make.lower()
        model_lower = model.lower()
        
        msrp = 1000000.0  # Fallback default: ₹10,00,000
        
        if "maruti" in make_lower or "swift" in model_lower:
            msrp = 700000.0
        elif "hyundai" in make_lower or "i20" in model_lower:
            msrp = 850000.0
        elif "honda" in make_lower or "city" in model_lower:
            msrp = 1400000.0
        elif "tata" in make_lower or "nexon" in model_lower:
            msrp = 1100000.0
        elif "mahindra" in make_lower or "xuv" in model_lower:
            msrp = 1800000.0
            
        # 2. Age-based compounding depreciation (12% per year)
        current_year = 2026
        age_years = max(0, current_year - year)
        depreciation_rate = 0.12
        
        # Compound formula: MSRP * (1 - rate)^age
        age_depreciated_value = msrp * ((1.0 - depreciation_rate) ** age_years)
        
        # Minimum residual age value: 15% of MSRP
        min_age_value = msrp * 0.15
        if age_depreciated_value < min_age_value:
            age_depreciated_value = min_age_value
            
        # 3. Odometer-based depreciation (₹2.50 per km driven)
        mileage_penalty = reported_odometer * 2.50
        
        # Cap mileage penalty at 40% of the age-depreciated value to preserve residual worth
        max_mileage_penalty = age_depreciated_value * 0.40
        if mileage_penalty > max_mileage_penalty:
            mileage_penalty = max_mileage_penalty
            
        base_worth = age_depreciated_value - mileage_penalty
        
        # 4. Odometer Fraud Probability Penalty (up to 35% penalty)
        # Higher fraud risk drops value due to engine health uncertainty and lack of warranty
        fraud_penalty_ratio = (fraud_probability / 100.0) * 0.35
        fraud_penalty = base_worth * fraud_penalty_ratio
        
        # 5. Visual Wear CNN Penalty (up to 10% penalty)
        # Based on interior pedal, steering, and seat degradation (0-10)
        wear_penalty_ratio = (average_wear_score / 10.0) * 0.10
        wear_penalty = base_worth * wear_penalty_ratio
        
        # 6. Dents & Scratches Restoration Penalty
        # Direct subtraction of repair/refurbishment costs
        damage_penalty = 0.0
        dents_lower = dents_scratches.lower()
        if "mild" in dents_lower:
            damage_penalty = 15000.0
        elif "moderate" in dents_lower:
            damage_penalty = 35000.0
        elif "severe" in dents_lower:
            damage_penalty = 75000.0
            
        # 7. Paint Thickness Repainting Penalty (8% penalty)
        # Thickness > 7.0 mils suggests structural panel repainting/crash repair
        repaint_detected = paint_thickness > 7.0
        repaint_penalty = 0.0
        if repaint_detected:
            repaint_penalty = base_worth * 0.08
            
        # 7.5 Insurance Penalties (Expiry & Claims History)
        insurance_penalty = 0.0
        if insurance_is_expired:
            insurance_penalty = 12000.0  # Comprehensive policy renewal cost
            
        insurance_claim_penalty = 0.0
        if insurance_claims_total_amount > 0:
            insurance_claim_penalty = base_worth * 0.08  # Accident history depreciation
            if insurance_claims_total_amount > 100000.0:
                insurance_claim_penalty += base_worth * 0.07  # Major accident severity penalty
                
        # 8. Calculate Final Worth
        actual_worth = base_worth - fraud_penalty - wear_penalty - damage_penalty - repaint_penalty - insurance_penalty - insurance_claim_penalty
        
        # Cap minimum worth at 12% of MSRP (scrap value)
        min_residual_worth = msrp * 0.12
        if actual_worth < min_residual_worth:
            actual_worth = min_residual_worth
            
        actual_worth = round(actual_worth, 2)
        
        # 9. Determine deal quality status if asking price is provided
        valuation_status = "NOT AVAILABLE"
        price_difference = 0.0
        
        if asking_price is not None and asking_price > 0:
            price_difference = round(asking_price - actual_worth, 2)
            deviation_ratio = price_difference / actual_worth
            
            if fraud_probability > 60.0:
                valuation_status = "SUSPECT SCAM"
            elif deviation_ratio > 0.05:
                valuation_status = "OVERPRICED"
            elif deviation_ratio < -0.05:
                valuation_status = "GOOD DEAL"
            else:
                valuation_status = "FAIR PRICE"
                
        return {
            "original_msrp": round(msrp, 2),
            "age_depreciated_value": round(age_depreciated_value, 2),
            "mileage_penalty": round(mileage_penalty, 2),
            "base_worth": round(base_worth, 2),
            "fraud_penalty": round(fraud_penalty, 2),
            "wear_penalty": round(wear_penalty, 2),
            "damage_penalty": round(damage_penalty, 2),
            "repaint_penalty": round(repaint_penalty, 2),
            "repaint_detected": repaint_detected,
            "insurance_expired_penalty": round(insurance_penalty, 2),
            "insurance_claim_penalty": round(insurance_claim_penalty, 2),
            "actual_worth": actual_worth,
            "asking_price": asking_price,
            "price_difference": price_difference,
            "valuation_status": valuation_status
        }
