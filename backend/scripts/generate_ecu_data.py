import os
import random
import csv
import pandas as pd
import numpy as np

def generate_synthetic_data(output_path: str, n_samples: int = 10000):
    print(f"Generating {n_samples} synthetic ECU vehicle records...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    headers = [
        "vin", "reported_odometer", "ecu_ecm", "ecu_tcm", "ecu_abs", 
        "ecu_airbag", "ecu_cluster", "engine_hours", "max_variance", 
        "avg_speed", "is_tampered"
    ]
    
    records = []
    
    for i in range(n_samples):
        vin = f"MA3ERLF3800{i:06d}"
        
        # 1. Decide if this record represents tampering (30% probability)
        is_tampered = 1 if random.random() < 0.30 else 0
        
        # True mileage of the vehicle
        true_mileage = random.randint(15000, 180000)
        
        # Average speed (km/h) - typically 25 to 60 for city/highway mix
        true_speed = random.uniform(30.0, 55.0)
        engine_hours = round(true_mileage / true_speed, 2)
        
        if is_tampered:
            # Instrument cluster is rolled back
            reported_odometer = random.randint(15000, max(20000, true_mileage - 25000))
            
            # Reprogramming patterns:
            # Pattern A: Only cluster is rolled back (amateur rollback - 50% of fraud)
            # Pattern B: Cluster + Airbag is rolled back, but ECM/TCM/ABS remain actual (30% of fraud)
            # Pattern C: Cluster + ABS + Airbag are rolled back, but ECM/TCM remain actual (20% of fraud)
            pattern = random.choice(["A", "B", "C"])
            
            ecu_cluster = reported_odometer
            
            if pattern == "A":
                ecu_ecm = true_mileage + random.randint(-150, 150)
                ecu_tcm = true_mileage + random.randint(-150, 150)
                ecu_abs = true_mileage + random.randint(-150, 150)
                ecu_airbag = true_mileage + random.randint(-150, 150)
            elif pattern == "B":
                ecu_ecm = true_mileage + random.randint(-150, 150)
                ecu_tcm = true_mileage + random.randint(-150, 150)
                ecu_abs = true_mileage + random.randint(-150, 150)
                ecu_airbag = reported_odometer + random.randint(-150, 150)
            else:  # Pattern C
                ecu_ecm = true_mileage + random.randint(-150, 150)
                ecu_tcm = true_mileage + random.randint(-150, 150)
                ecu_abs = reported_odometer + random.randint(-150, 150)
                ecu_airbag = reported_odometer + random.randint(-150, 150)
        else:
            # Clean record - all modules align close to the reported mileage
            reported_odometer = true_mileage
            ecu_cluster = true_mileage + random.randint(-200, 200)
            ecu_ecm = true_mileage + random.randint(-200, 200)
            ecu_tcm = true_mileage + random.randint(-200, 200)
            ecu_abs = true_mileage + random.randint(-200, 200)
            ecu_airbag = true_mileage + random.randint(-200, 200)
            
        # Clip minimum mileage at 0
        reported_odometer = max(0, reported_odometer)
        ecu_cluster = max(0, ecu_cluster)
        ecu_ecm = max(0, ecu_ecm)
        ecu_tcm = max(0, ecu_tcm)
        ecu_abs = max(0, ecu_abs)
        ecu_airbag = max(0, ecu_airbag)
        
        # Calculate engineered features
        module_readings = [ecu_cluster, ecu_ecm, ecu_tcm, ecu_abs, ecu_airbag]
        max_variance = max(module_readings) - min(module_readings)
        
        # Average speed based on reported odometer
        # If odometer was rolled back but engine hours not, average speed will be suspiciously low
        avg_speed = round(reported_odometer / max(0.1, engine_hours), 2)
        
        records.append([
            vin, reported_odometer, ecu_ecm, ecu_tcm, ecu_abs, 
            ecu_airbag, ecu_cluster, engine_hours, max_variance, 
            avg_speed, is_tampered
        ])
        
    with open(output_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)
        
    print(f"Dataset successfully created and saved to {output_path}")

if __name__ == "__main__":
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "ecu_training_data.csv"))
    generate_synthetic_data(csv_path)
