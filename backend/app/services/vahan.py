from datetime import datetime, date
import random
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.database import Vehicle, VahanRecord

class VahanService:
    @staticmethod
    def get_or_create_mock_vahan_records(db: Session, vin: str, current_odometer: int) -> Tuple[Vehicle, List[VahanRecord]]:
        """
        Looks up a vehicle in the database. If not found, generates a realistic (or anomalous)
        mock VAHAN history to make the demo fully functional for any input.
        """
        vehicle = db.query(Vehicle).filter(Vehicle.vin == vin).first()
        
        if not vehicle:
            # Create a mock vehicle
            makes_models = [
                ("Maruti Suzuki", "Swift"),
                ("Hyundai", "i20"),
                ("Honda", "City"),
                ("Tata", "Nexon"),
                ("Mahindra", "XUV500")
            ]
            make, model = random.choice(makes_models)
            year = random.randint(2015, 2022)
            
            # Register date in the past
            reg_year = year
            reg_month = random.randint(1, 12)
            reg_day = random.randint(1, 28)
            registered_date = date(reg_year, reg_month, reg_day)
            
            # Mock insurance details
            insurers = ["HDFC ERGO", "ICICI Lombard", "Tata AIG", "Bajaj Allianz", "SBI General"]
            company = random.choice(insurers)
            policy_no = f"POL-{random.randint(100000, 999999)}"
            
            # Expired insurance in 15% of cases, or if VIN ends with '7'
            is_expired_case = vin.endswith("7") or (random.random() < 0.15)
            if is_expired_case:
                # Expired between 10 and 90 days ago
                days_ago = random.randint(10, 90)
                expiry_date = date.today() - timedelta_days(days_ago)
            else:
                # Valid for next 30 to 300 days
                days_ahead = random.randint(30, 300)
                expiry_date = date.today() + timedelta_days(days_ahead)
                
            # Claims: tampered vehicles or vehicles with specific suffix have accident history
            is_accident_case = vin.endswith(("C", "Z")) or (random.random() < 0.20)
            if is_accident_case:
                claims_count = random.choice([1, 2])
                claims_amount = round(random.uniform(25000.0, 180000.0), 2)
                ncb = 0
            else:
                claims_count = 0
                claims_amount = 0.0
                ncb = random.choice([20, 25, 35, 50])
                
            vehicle = Vehicle(
                vin=vin,
                make=make,
                model=model,
                year=year,
                current_owner=random.choice([1, 2, 3]),
                registered_date=registered_date,
                registration_city=random.choice(["Mumbai", "Delhi", "Bengaluru", "Pune", "Chennai", "Hyderabad"]),
                insurance_company=company,
                insurance_policy_number=policy_no,
                insurance_expiry_date=expiry_date,
                insurance_claims_count=claims_count,
                insurance_claims_total_amount=claims_amount,
                insurance_no_claim_bonus=ncb
            )
            db.add(vehicle)
            db.commit()
            db.refresh(vehicle)
            
            # Generate historical VAHAN odometer logs
            # Let's decide if this specific vehicle will simulate tampering
            # We can use the VIN's last digit or random choice to decide if it's fraud
            is_tampered_vin = vin.endswith(("7", "9", "X", "Z"))  # ~40% of mock cases
            
            historical_records = []
            num_records = random.randint(2, 4)
            
            # We want to build a timeline
            start_date = datetime.combine(registered_date, datetime.min.time())
            now = datetime.now()
            days_span = (now - start_date).days
            
            # Distribute dates
            date_checkpoints = []
            for _ in range(num_records):
                days_offset = random.randint(30, max(60, days_span - 30))
                date_checkpoints.append(start_date + timedelta_days(days_offset))
            date_checkpoints.sort()
            
            # Generate incremental mileage
            last_mileage = random.randint(5000, 15000)
            for i, record_date in enumerate(date_checkpoints):
                owner_number = 1 if i < 2 else 2
                
                # If tampered, let's create a drop in history or make the last history higher than current_odometer
                if is_tampered_vin and i == len(date_checkpoints) - 1:
                    # Let's make a rollback drop
                    odometer_reading = last_mileage + random.randint(15000, 25000)
                    # The next step (or user input) will be lower
                else:
                    odometer_reading = last_mileage + random.randint(8000, 15000)
                
                last_mileage = odometer_reading
                
                vahan_rec = VahanRecord(
                    vehicle_id=vehicle.vehicle_id,
                    recorded_date=record_date.date(),
                    odometer_reading=odometer_reading,
                    owner_number=owner_number,
                    api_response={"status": "success", "source": "parivahan_api_mock"}
                )
                db.add(vahan_rec)
                historical_records.append(vahan_rec)
            
            db.commit()
        
        # Load records sorted by date
        records = db.query(VahanRecord).filter(VahanRecord.vehicle_id == vehicle.vehicle_id).order_by(VahanRecord.recorded_date.asc()).all()
        return vehicle, records

    @staticmethod
    def analyze_timeline(historical_records: List[VahanRecord], current_odometer: int) -> Dict[str, Any]:
        """
        Analyzes the odometer readings timeline for:
        1. Historical drops (e.g. odometer value decreases over time).
        2. Discrepancy between current odometer and latest historical record.
        """
        timeline = []
        for rec in historical_records:
            timeline.append({
                "date": rec.recorded_date.strftime("%Y-%m-%d"),
                "odometer": rec.odometer_reading,
                "owner_number": rec.owner_number
            })
            
        # Add current transaction to the analysis timeline
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        timeline.append({
            "date": current_date_str,
            "odometer": current_odometer,
            "owner_number": "Current (Reported)"
        })
        
        # Sort checklist-style to check for drops
        # Sort chronologically by parsing date strings
        sorted_timeline = sorted(timeline, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))
        
        vahan_score = 0.0
        anomalies = []
        max_historical_reading = 0
        
        # Check historical records
        for i in range(1, len(sorted_timeline)):
            prev = sorted_timeline[i-1]
            curr = sorted_timeline[i]
            
            if curr["odometer"] < prev["odometer"]:
                drop_amount = prev["odometer"] - curr["odometer"]
                anomalies.append({
                    "type": "odometer_rollback",
                    "description": f"Odometer dropped from {prev['odometer']:,} km on {prev['date']} to {curr['odometer']:,} km on {curr['date']}.",
                    "drop_km": drop_amount
                })
                # Drop scale: absolute drop creates a heavy score
                vahan_score = max(vahan_score, 100.0)
            
            # Keep track of the highest reading in history
            if prev["owner_number"] != "Current (Reported)":
                max_historical_reading = max(max_historical_reading, prev["odometer"])
        
        # If current odometer is less than the maximum historical reading
        if current_odometer < max_historical_reading:
            drop_amount = max_historical_reading - current_odometer
            anomalies.append({
                "type": "current_reading_rollback",
                "description": f"Reported odometer ({current_odometer:,} km) is lower than previous history record of {max_historical_reading:,} km.",
                "drop_km": drop_amount
            })
            vahan_score = 100.0

        # If no hard drops, check if the mileage growth is abnormally flat or slow (suspicious but not definitive)
        if vahan_score == 0 and len(historical_records) >= 2:
            first_rec = historical_records[0]
            last_rec = historical_records[-1]
            days = (last_rec.recorded_date - first_rec.recorded_date).days
            if days > 0:
                km_per_year = ((last_rec.odometer_reading - first_rec.odometer_reading) / days) * 365
                if km_per_year < 1000:  # Suspiciously low average annual driving
                    vahan_score = 25.0
                    anomalies.append({
                        "type": "low_mileage_accumulation",
                        "description": f"Extremely low mileage accumulation detected: averaging {int(km_per_year):,} km per year."
                    })
        
        return {
            "vahan_score": vahan_score,
            "timeline": sorted_timeline,
            "anomalies": anomalies,
            "has_rollback": vahan_score >= 100.0,
            "sufficient_history": len(historical_records) >= 2
        }

def timedelta_days(days: int) -> datetime:
    from datetime import timedelta
    return timedelta(days=days)
