import requests
import logging
from typing import Dict, Any, Optional
from backend.app.config import settings

logger = logging.getLogger(__name__)

class LlmReportService:
    @staticmethod
    def generate_report(
        vehicle_details: Dict[str, Any],
        vahan_summary: Dict[str, Any],
        ecu_summary: Dict[str, Any],
        xgboost_summary: Dict[str, Any],
        wear_summary: Dict[str, Any],
        final_score: float,
        risk_level: str,
        recommendation: str,
        valuation_result: Optional[Dict[str, Any]] = None,
        insurance_summary: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates a 200-300 word inspection fraud report.
        Tries to call Hugging Face Serverless Inference API.
        Falls back to a dynamic local template generator if Hugging Face is unavailable.
        """
        vin = vehicle_details.get("vin")
        make = vehicle_details.get("make")
        model = vehicle_details.get("model")
        year = vehicle_details.get("year")
        
        # Format metrics summary for LLM context
        prompt_content = (
            f"Vehicle: {year} {make} {model} (VIN: {vin})\n"
            f"Final Odometer Fraud Risk Score: {final_score}% ({risk_level})\n"
            f"System Recommendation: {recommendation}\n"
            f"- Layer 1 (VAHAN History): Timeline anomalies: {len(vahan_summary.get('anomalies', []))} found. "
            f"VAHAN Score: {vahan_summary.get('vahan_score')}/100.\n"
            f"- Layer 2 (ECU Consistency): ECU mileage discrepancy: {ecu_summary.get('variance_km')} km. "
            f"Reported average speed: {ecu_summary.get('avg_speed_kmh')} km/h. ECU Score: {ecu_summary.get('ecu_score')}/100.\n"
            f"- Layer 3 (XGBoost Classifier): ML fraud probability: {xgboost_summary.get('xgboost_score')}%.\n"
            f"- Layer 4 (Physical Wear CNN): Wear levels - Pedal: {wear_summary.get('pedal', {}).get('wear_level')}, "
            f"Steering: {wear_summary.get('steering', {}).get('wear_level')}, Seat: {wear_summary.get('seat', {}).get('wear_level')}. "
            f"Average Wear Score: {wear_summary.get('average_wear_score')}/10.\n"
        )
        
        if valuation_result:
            prompt_content += (
                f"- Fair Market Worth: ₹{valuation_result.get('actual_worth'):,.2f} "
                f"(Asking Price: ₹{valuation_result.get('asking_price', 0.0):,.2f}, "
                f"Status: {valuation_result.get('valuation_status')}).\n"
                f"- Damage Check: Dents/Scratches: {valuation_result.get('dents_scratches')}. "
                f"Paint Thickness: {valuation_result.get('paint_thickness', 5.0)} mils. Repaint detected: {valuation_result.get('repaint_detected')}.\n"
            )
        
        if insurance_summary:
            prompt_content += (
                f"- Layer 7 (Insurance Check): Company: {insurance_summary.get('insurance_company')}, "
                f"Policy: {insurance_summary.get('policy_number')}, Status: {insurance_summary.get('status')}, "
                f"Claims: {insurance_summary.get('claims_count')} (Total: ₹{insurance_summary.get('claims_total_amount'):,.2f}), "
                f"NCB: {insurance_summary.get('no_claim_bonus_percentage')}%.\n"
            )
        
        # If API token is configured, try Hugging Face
        if settings.HF_API_KEY:
            try:
                headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
                api_url = f"https://api-inference.huggingface.co/models/{settings.HF_MODEL_ID}"
                
                # Instruction payload
                payload = {
                    "inputs": (
                        f"<|system|>\nYou are OdoShield AI, an expert automotive forensic auditor. "
                        f"Write a concise, professional 200-300 word odometer fraud analysis report based on the following diagnostic metrics. "
                        f"Write in clear paragraphs, outlining findings, evidence of tampering, and why the recommendation was made.\n"
                        f"<|user|>\n{prompt_content}\n<|assistant|>\n"
                    ),
                    "parameters": {
                        "max_new_tokens": 300,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                }
                
                response = requests.post(api_url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    # HF returns a list or dict depending on configuration
                    if isinstance(result, list) and len(result) > 0:
                        report_text = result[0].get("generated_text", "").strip()
                    elif isinstance(result, dict):
                        report_text = result.get("generated_text", "").strip()
                    else:
                        report_text = str(result)
                        
                    if report_text:
                        return report_text
                else:
                    logger.warning(f"HF API returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to query Hugging Face API: {e}")
                
        # Dynamic template-based local fallback if Hugging Face fails/not configured
        logger.info("Using local template report generator.")
        return LlmReportService._generate_local_report(
            make, model, year, vin, final_score, risk_level, recommendation,
            vahan_summary, ecu_summary, xgboost_summary, wear_summary, valuation_result, insurance_summary
        )

    @staticmethod
    def _generate_local_report(
        make: str, model: str, year: int, vin: str, final_score: float, risk_level: str, recommendation: str,
        vahan_summary: Dict[str, Any], ecu_summary: Dict[str, Any], xgboost_summary: Dict[str, Any], wear_summary: Dict[str, Any],
        valuation_result: Optional[Dict[str, Any]] = None,
        insurance_summary: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compiles a high-quality, professional markdown report based on diagnostic findings.
        """
        report = []
        report.append(f"### OdoShield Automotive Forensic Audit Report")
        report.append(f"**Vehicle Identity:** {year} {make} {model} | **VIN:** `{vin}`\n")
        
        report.append(f"**Verification Status:** **{recommendation}** | **Fraud Risk Probability:** {final_score}% ({risk_level})")
        report.append("---")
        
        # Section 1: Findings Overview
        report.append("#### Executive Summary")
        if final_score < 30:
            report.append(
                f"A comprehensive forensic audit of the vehicle `{vin}` indicates a low probability of odometer manipulation. "
                f"Data logs across all primary vehicle components, electronic control units, and registration timelines "
                f"appear uniform and consistent with legitimate vehicle aging. The reported mileage is deemed credible."
            )
        elif final_score < 70:
            report.append(
                f"A medium fraud risk has been flagged for this vehicle. Discrepancies were noted between electronic module data "
                f"or historical records and physical wear. While odometer tampering is not definitively proven, "
                f"sufficient variance exists to suggest secondary investigation and professional mechanical inspection is warranted before purchase."
            )
        else:
            report.append(
                f"**CRITICAL TAMPERING WARNING:** OdoShield forensic analysis indicates a high probability of odometer fraud. "
                f"Multiple layers of diagnostic indicators, including electronic module mismatches and registration odometer rollbacks, "
                f"suggest active manipulation of the primary instrument cluster odometer. The vehicle is not recommended for purchase in its current state."
            )
            
        # Section 2: Evidentiary Breakdown
        report.append("#### Evidentiary Analysis")
        
        # Layer 1 evidence
        if vahan_summary.get("vahan_score", 0) >= 100:
            anomalies = vahan_summary.get("anomalies", [])
            desc = anomalies[0].get("description") if anomalies else "Odometer rollback found in registration records."
            report.append(f"- **Layer 1 (VAHAN History):** {desc} (Tampering verified chronologically).")
        else:
            report.append("- **Layer 1 (VAHAN History):** Chronological registration odometer timeline is consistent.")
            
        # Layer 2 evidence
        ecu_var = ecu_summary.get("variance_km", 0)
        if ecu_var > 500:
            report.append(
                f"- **Layer 2 (ECU Variance):** Electronic Module discrepancy of **{ecu_var:,} km** detected. "
                f"Instrument cluster reading does not match primary engine/transmission logs. "
                f"Usually, discrepancies exceeding 500 km signify dashboard reprogramming."
            )
        else:
            report.append(f"- **Layer 2 (ECU Variance):** Digital module variance is within normal tolerances ({ecu_var} km).")
            
        # Speed & Hours evidence
        if ecu_summary.get("engine_hours_anomaly"):
            report.append(f"- **Layer 2 (Engine Hours):** {ecu_summary.get('hours_description')}")
            
        # Layer 3 (XGBoost) evidence
        xgb_prob = xgboost_summary.get("xgboost_score", 0)
        if xgb_prob > 50:
            report.append(f"- **Layer 3 (ML Classifier):** XGBoost fraud probability is high ({xgb_prob}%).")
            
        # Layer 4 (Physical Wear) evidence
        avg_wear = wear_summary.get("average_wear_score", 0)
        report.append(
            f"- **Layer 4 (Physical Wear):** Average wear index is **{avg_wear}/10**. "
            f"Pedals: {wear_summary.get('pedal', {}).get('wear_level')}, "
            f"Steering Wheel: {wear_summary.get('steering', {}).get('wear_level')}, "
            f"Seats: {wear_summary.get('seat', {}).get('wear_level')}."
        )
        
        # Section 3: Recommendation
        report.append("#### Audit Recommendation")
        if recommendation == "ACCEPT":
            report.append("The vehicle presents clean history metrics. Accept transaction. Proceed with standard inspection.")
        elif recommendation == "REVIEW":
            report.append("The vehicle displays moderate warning signs. Request full workshop OBD-II scanning logs and physical maintenance records before proceeding.")
        else:
            report.append("Odometer fraud detected. Reject transaction. Do not purchase without correcting the actual mileage and verifying mechanical safety.")
            
        # Section 3.5: Insurance Status
        if insurance_summary:
            report.append("#### Layer 7: Insurance & Claims Verification")
            report.append(
                f"- **Insurer:** {insurance_summary.get('insurance_company')} | **Policy Number:** `{insurance_summary.get('policy_number')}`\n"
                f"- **Status:** **{insurance_summary.get('status')}** (Expires: {insurance_summary.get('expiry_date')})\n"
                f"- **Claims Record:** {insurance_summary.get('claims_count')} claim(s) filed. Total claimed amount: **₹{insurance_summary.get('claims_total_amount'):,.2f}**\n"
                f"- **No Claim Bonus (NCB):** **{insurance_summary.get('no_claim_bonus_percentage')}%**"
            )
            
            if insurance_summary.get("is_expired"):
                report.append(f"> [!WARNING]\n> **Insurance Policy is Expired!** Driving the vehicle is illegal. A renewal cost penalty has been deducted from the valuation.")
            if insurance_summary.get("claims_count", 0) > 0:
                report.append(f"> [!IMPORTANT]\n> **Accident Claims Recorded:** A total claim amount of ₹{insurance_summary.get('claims_total_amount'):,.2f} indicates past body repair work. Ensure structural alignment is verified.")
            
        # Section 4: Valuation & Buyer Negotiation Suggestions
        if valuation_result:
            report.append("#### Buyer Suggestions & Negotiation Strategy")
            
            actual_worth = valuation_result.get("actual_worth", 0.0)
            asking_price = valuation_result.get("asking_price")
            status = valuation_result.get("valuation_status", "NOT AVAILABLE")
            repaint_detected = valuation_result.get("repaint_detected", False)
            
            # Retrieve odometer reading safely
            try:
                reported_odo = int(vahan_summary["timeline"][-1]["odometer"])
            except:
                reported_odo = 0
            
            # 1. Price analysis
            if asking_price:
                diff = asking_price - actual_worth
                if status == "GOOD DEAL":
                    report.append(
                        f"- **Deal Evaluation:** The asking price of **₹{asking_price:,.2f}** is below the fair market valuation of **₹{actual_worth:,.2f}**. "
                        f"This is a **GOOD DEAL** (undervalued by ₹{abs(diff):,.2f}). Proceed with transaction checks."
                    )
                elif status == "OVERPRICED":
                    report.append(
                        f"- **Price Penalty:** The asking price of **₹{asking_price:,.2f}** is **OVERPRICED** by **₹{diff:,.2f}** "
                        f"compared to OdoShield's actual worth calculation of **₹{actual_worth:,.2f}**. Use this gap directly for price negotiation."
                    )
                elif status == "SUSPECT SCAM":
                    report.append(
                        f"- **SCAM WARNING:** The vehicle has a very high odometer fraud probability. "
                        f"Even though the seller asks ₹{asking_price:,.2f}, the integrity risk drops the vehicle worth to **₹{actual_worth:,.2f}**. "
                        f"**Do not buy** at this price unless deep mechanical auditing proves odometer consistency."
                    )
                else:
                    report.append(
                        f"- **Deal Evaluation:** The asking price of **₹{asking_price:,.2f}** is inline with the fair worth of **₹{actual_worth:,.2f}** (**FAIR PRICE**)."
                    )
            else:
                report.append(f"- **Fair Worth Assessment:** The calculated fair market value of this vehicle is **₹{actual_worth:,.2f}** based on current wear and mileage parameters.")

            # 2. Specific Negotiation Points
            report.append("##### Key Leverage Points for Negotiation:")
            leverage_count = 0
            
            # Odo rollback leverage
            if final_score > 50.0:
                report.append(
                    f"- **Odometer Rollback Risk:** The AI aggregator calculated a **{final_score}% fraud probability**. "
                    f"Point out the electronic registers inconsistencies or VAHAN rollback logs to demand a major price reduction."
                )
                leverage_count += 1
                
            # ECU discrepancy leverage
            ecu_var = ecu_summary.get("variance_km", 0)
            if ecu_var > 500:
                report.append(
                    f"- **Electronic Register Mismatch:** OBD scans show a module mileage discrepancy of **{ecu_var:,} km** between cluster and registers. "
                    f"Point out that the instrument cluster has likely been reflashed or replaced."
                )
                leverage_count += 1
                
            # Paint thickness repaint leverage
            if repaint_detected:
                report.append(
                    f"- **Accident History & Paint Thickness:** Paint thickness reading is high. "
                    f"This indicates body panel repainting and previous collision repair. Demand proof of structural crash alignment and use it to ask for discount."
                )
                leverage_count += 1
                
            # High wear mismatch leverage
            avg_wear = wear_summary.get("average_wear_score", 0)
            if avg_wear > 6.0 and reported_odo < 50000:
                report.append(
                    f"- **Interior Cosmetic Refurbishment:** Physical wear is high ({avg_wear}/10) despite low odometer reading. "
                    f"Bring up this obvious wear mismatch to challenge the seller's mileage claim."
                )
                leverage_count += 1
                
            # Insurance claim leverage
            if insurance_summary:
                claims_count = insurance_summary.get("claims_count", 0)
                claims_total = insurance_summary.get("claims_total_amount", 0.0)
                if claims_count > 0:
                    report.append(
                        f"- **Accident Claims History:** Insurer records reveal {claims_count} accident claim(s) totaling **₹{claims_total:,.2f}**. "
                        f"Use this evidence to negotiate a discount for collision-based depreciation."
                    )
                    leverage_count += 1
                    
                # Expired insurance leverage
                if insurance_summary.get("is_expired"):
                    report.append(
                        f"- **Expired Insurance Policy:** The policy expired on {insurance_summary.get('expiry_date')}. "
                        f"Demand a discount of at least ₹12,000 to cover the immediate comprehensive policy renewal cost."
                    )
                    leverage_count += 1
                    
            if leverage_count == 0:
                report.append("- No negative discrepancies detected. Vehicle is in clean, market-aligned condition.")
            
        return "\n\n".join(report)
