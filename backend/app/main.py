import os
import logging
from typing import Optional
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, date

from backend.app.config import settings
from backend.app.database import get_db, init_db, Vehicle, EcuReading, WearImage, FraudScore
from backend.app.services.vahan import VahanService
from backend.app.services.ecu import EcuService
from backend.app.services.xgboost_model import XGBoostService
from backend.app.services.wear_cnn import WearCnnService
from backend.app.services.llm_report import LlmReportService
from backend.app.services.score_aggregator import ScoreAggregatorService
from backend.app.services.valuation import ValuationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="OdoShield Odometer Fraud Detection API - 6-Layer Verification"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
@app.on_event("startup")
def startup_event():
    init_db()

# Main vehicle verification endpoint
@app.post("/api/v1/verify-vehicle")
async def verify_vehicle(
    vin: str = Form(...),
    current_odometer: int = Form(...),
    engine_hours: float = Form(2000.0),
    ecu_ecm: Optional[int] = Form(None),
    ecu_tcm: Optional[int] = Form(None),
    ecu_abs: Optional[int] = Form(None),
    ecu_airbag: Optional[int] = Form(None),
    ecu_cluster: Optional[int] = Form(None),
    image_pedal: Optional[UploadFile] = File(None),
    image_steering: Optional[UploadFile] = File(None),
    image_seat: Optional[UploadFile] = File(None),
    asking_price: Optional[float] = Form(None),
    paint_thickness: float = Form(5.0),
    dents_scratches: str = Form("None"),
    car_color: str = Form("White"),
    db: Session = Depends(get_db)
):
    try:
        vin = vin.strip().upper()
        if len(vin) != 17:
            raise HTTPException(status_code=400, detail="VIN must be exactly 17 characters long.")
            
        logger.info(f"Processing verification request for VIN: {vin}, Odometer: {current_odometer} km")
        
        # 1. Fetch or create VAHAN History (Layer 1)
        vehicle, vahan_records = VahanService.get_or_create_mock_vahan_records(db, vin, current_odometer)
        vahan_summary = VahanService.analyze_timeline(vahan_records, current_odometer)
        
        # 2. Setup ECU readings (Layer 2)
        # Use provided readings or default close to reported odometer
        ecu_readings_map = {
            "ECM": ecu_ecm if ecu_ecm is not None else current_odometer,
            "TCM": ecu_tcm if ecu_tcm is not None else current_odometer,
            "ABS": ecu_abs if ecu_abs is not None else current_odometer,
            "AIRBAG": ecu_airbag if ecu_airbag is not None else current_odometer,
            "CLUSTER": ecu_cluster if ecu_cluster is not None else current_odometer,
        }
        
        # Save ECU readings to database
        for mod, val in ecu_readings_map.items():
            reading = EcuReading(
                vehicle_id=vehicle.vehicle_id,
                ecu_module=mod,
                mileage=val,
                engine_hours=engine_hours
            )
            db.add(reading)
            
        ecu_summary = EcuService.analyze_ecu_consistency(ecu_readings_map, engine_hours, current_odometer)
        
        # 3. XGBoost classifier probability (Layer 3)
        xgboost_summary = XGBoostService.predict_fraud(current_odometer, ecu_readings_map, engine_hours)
        
        # 4. Physical Wear CNN classification (Layer 4)
        components = {
            "pedal": image_pedal,
            "steering": image_steering,
            "seat": image_seat
        }
        
        wear_results = {}
        total_wear_score = 0.0
        
        for comp_name, file_obj in components.items():
            wear_score = 3.0  # default LOW wear if no image uploaded
            wear_level = "LOW"
            image_url = "default_avatar.jpg"
            
            if file_obj is not None:
                content = await file_obj.read()
                # Run PyTorch CNN classifier
                res = WearCnnService.analyze_component_wear(content, comp_name)
                wear_score = res["wear_score"]
                wear_level = res["wear_level"]
                image_url = f"/static/uploads/{vin}_{comp_name}.jpg"
                
                # Mock file writing for visualization
                os.makedirs("backend/static/uploads", exist_ok=True)
                with open(f"backend/static/uploads/{vin}_{comp_name}.jpg", "wb") as f:
                    f.write(content)
            else:
                # If no image uploaded, generate plausible wear based on odometer reading
                # E.g. high odometer = higher mock wear
                base_prob = min(9.5, max(0.5, (current_odometer / 180000.0) * 10.0))
                wear_score = round(base_prob + (2.0 if vin.endswith(("7","9","X","Z")) else -1.0), 2)
                wear_score = min(10.0, max(0.0, wear_score))
                
                if wear_score < 3.5:
                    wear_level = "LOW"
                elif wear_score < 7.0:
                    wear_level = "MEDIUM"
                else:
                    wear_level = "HIGH"
                    
            # Save wear image record
            wear_rec = WearImage(
                vehicle_id=vehicle.vehicle_id,
                component=comp_name,
                image_url=image_url,
                wear_score=wear_score,
                wear_level=wear_level
            )
            db.add(wear_rec)
            
            wear_results[comp_name] = {
                "wear_score": wear_score,
                "wear_level": wear_level,
                "image_url": image_url
            }
            total_wear_score += wear_score
            
        avg_wear_score = round(total_wear_score / 3.0, 2)
        wear_summary = {
            "pedal": wear_results["pedal"],
            "steering": wear_results["steering"],
            "seat": wear_results["seat"],
            "average_wear_score": avg_wear_score
        }
        
        # 5. Aggregate final scores (Layer 6)
        agg_result = ScoreAggregatorService.aggregate_scores(
            vahan_score=vahan_summary["vahan_score"],
            ecu_score=ecu_summary["ecu_score"],
            xgboost_score=xgboost_summary["xgboost_score"],
            average_wear_score=avg_wear_score,
            reported_odometer=current_odometer,
            sufficient_history=vahan_summary["sufficient_history"]
        )
        
        # Analyze insurance status and claims
        today = date.today()
        is_expired = False
        days_diff = 0
        if vehicle.insurance_expiry_date:
            is_expired = vehicle.insurance_expiry_date < today
            days_diff = abs((vehicle.insurance_expiry_date - today).days)
            
        insurance_status = "VALID"
        if is_expired:
            insurance_status = "EXPIRED"
        elif not vehicle.insurance_policy_number:
            insurance_status = "NO_INSURANCE"
            
        insurance_alerts = []
        if is_expired:
            insurance_alerts.append(f"Policy expired {days_diff} days ago (renewal required).")
        if vehicle.insurance_claims_count > 0:
            insurance_alerts.append(f"{vehicle.insurance_claims_count} accident claim(s) detected (Total: ₹{float(vehicle.insurance_claims_total_amount):,.2f}).")
        if vehicle.insurance_no_claim_bonus == 0 and vehicle.insurance_claims_count > 0:
            insurance_alerts.append("No Claim Bonus (NCB) reset to 0% due to claim history.")
            
        insurance_analysis = {
            "insurance_company": vehicle.insurance_company or "N/A",
            "policy_number": vehicle.insurance_policy_number or "N/A",
            "expiry_date": vehicle.insurance_expiry_date.strftime("%Y-%m-%d") if vehicle.insurance_expiry_date else "N/A",
            "is_expired": is_expired,
            "days_to_expiry_or_expired": days_diff,
            "claims_count": vehicle.insurance_claims_count,
            "claims_total_amount": float(vehicle.insurance_claims_total_amount),
            "no_claim_bonus_percentage": vehicle.insurance_no_claim_bonus,
            "status": insurance_status,
            "alerts": insurance_alerts
        }

        # 5.5 Calculate fair market worth valuation
        valuation_result = ValuationService.calculate_fair_value(
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            reported_odometer=current_odometer,
            fraud_probability=agg_result["combined_score"],
            average_wear_score=avg_wear_score,
            dents_scratches=dents_scratches,
            paint_thickness=paint_thickness,
            asking_price=asking_price,
            insurance_claims_total_amount=float(vehicle.insurance_claims_total_amount),
            insurance_is_expired=is_expired
        )
        
        # 6. Generate natural language report (Layer 5)
        llm_report = LlmReportService.generate_report(
            vehicle_details={
                "vin": vin,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": vehicle.year
            },
            vahan_summary=vahan_summary,
            ecu_summary=ecu_summary,
            xgboost_summary=xgboost_summary,
            wear_summary=wear_summary,
            final_score=agg_result["combined_score"],
            risk_level=agg_result["risk_level"],
            recommendation=agg_result["recommendation"],
            valuation_result=valuation_result,
            insurance_summary=insurance_analysis
        )
        
        # Save final fraud score details to database
        fraud_score = FraudScore(
            vehicle_id=vehicle.vehicle_id,
            vahan_score=agg_result["vahan_score"],
            ecu_score=agg_result["ecu_score"],
            xgboost_score=agg_result["xgboost_score"],
            wear_score=agg_result["wear_score"],
            combined_score=agg_result["combined_score"],
            fraud_probability=agg_result["fraud_probability"],
            risk_level=agg_result["risk_level"],
            recommendation=agg_result["recommendation"],
            llm_report=llm_report
        )
        db.add(fraud_score)
        db.commit()
        
        # Return response
        return {
            "vin": vin,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "registration_city": vehicle.registration_city,
            "current_owner_count": vehicle.current_owner,
            "reported_odometer": current_odometer,
            "fraud_probability": agg_result["fraud_probability"],
            "risk_level": agg_result["risk_level"],
            "recommendation": agg_result["recommendation"],
            "layer_scores": {
                "vahan_score": agg_result["vahan_score"],
                "ecu_score": agg_result["ecu_score"],
                "xgboost_score": agg_result["xgboost_score"],
                "wear_score": agg_result["wear_score"]
            },
            "vahan_analysis": {
                "timeline": vahan_summary["timeline"],
                "anomalies": vahan_summary["anomalies"]
            },
            "ecu_analysis": {
                "variance_km": ecu_summary["variance_km"],
                "avg_speed_kmh": ecu_summary["avg_speed_kmh"],
                "engine_hours_anomaly": ecu_summary["engine_hours_anomaly"],
                "hours_description": ecu_summary["hours_description"],
                "modules": ecu_summary["modules"],
                "outlier_detected": ecu_summary["outlier_detected"],
                "outlier_module": ecu_summary["outlier_module"],
                "outlier_description": ecu_summary["outlier_description"]
            },
            "wear_analysis": wear_summary,
            "valuation_analysis": valuation_result,
            "insurance_analysis": insurance_analysis,
            "llm_report": llm_report
        }
        
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Internal server error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Health check endpoint
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME
    }

# Serve Frontend static directory (pointing to public folder at root or frontend/public)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
static_dir = os.path.join(parent_dir, "public")

if not os.path.exists(static_dir):
    static_dir = os.path.join(parent_dir, "frontend", "public")

# Mount static files at root / so relative styles.css resolves correctly on port 8000
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
