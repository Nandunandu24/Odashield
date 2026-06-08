import os
import pandas as pd
import numpy as np
from scipy import stats

def perform_eda():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", "models", "ecu_training_data.csv")
    
    if not os.path.exists(data_path):
        print(f"[ERROR] Training data not found at {data_path}. Please run generate_ecu_data.py first.")
        return
        
    print(f"Loading vehicle dataset for Exploratory Data Analysis (EDA) from {data_path}...\n")
    df = pd.read_csv(data_path)
    
    # 1. Descriptive statistics
    print("--- 1. Descriptive Statistics ---")
    print(f"Total vehicle records: {len(df)}")
    print(f"Clean vehicles (is_tampered = 0): {len(df[df['is_tampered'] == 0])}")
    print(f"Tampered vehicles (is_tampered = 1): {len(df[df['is_tampered'] == 1])}")
    print(f"Base fraud rate: {df['is_tampered'].mean() * 100:.2f}%\n")
    
    # 2. Segment Analysis
    print("--- 2. Segment Profiles (Mean Values) ---")
    segments = df.groupby("is_tampered")[["reported_odometer", "max_variance", "engine_hours", "avg_speed"]].mean()
    print(segments.to_string())
    print("\n")
    
    # 3. Correlation Matrix
    print("--- 3. Correlation with Tampering (Target Variable) ---")
    correlations = df.corr(numeric_only=True)["is_tampered"].sort_values(ascending=False)
    for col, val in correlations.items():
        if col != "is_tampered" and col != "vin":
            print(f"{col:20} : Correlation = {val:.4f}")
    print("\n")
    
    # 4. Hypothesis Testing: Two-Sample Independent T-Test
    # Null Hypothesis (H0): The average speed calculated from engine hours is the same 
    # for clean vehicles and tampered vehicles.
    # Alternative Hypothesis (H1): The average speed of tampered vehicles is significantly
    # different (statistically lower) than clean vehicles due to odometer rollbacks.
    print("--- 4. Hypothesis Testing (Two-Sample Independent T-Test) ---")
    clean_speeds = df[df["is_tampered"] == 0]["avg_speed"]
    tampered_speeds = df[df["is_tampered"] == 1]["avg_speed"]
    
    t_stat, p_val = stats.ttest_ind(clean_speeds, tampered_speeds, equal_var=False)
    
    print(f"Clean Vehicles - Mean Avg Speed: {clean_speeds.mean():.2f} km/h (Std: {clean_speeds.std():.2f})")
    print(f"Tampered Vehicles - Mean Avg Speed: {tampered_speeds.mean():.2f} km/h (Std: {tampered_speeds.std():.2f})")
    print(f"Calculated T-Statistic: {t_stat:.4f}")
    print(f"Calculated P-Value: {p_val:.4e}")
    
    alpha = 0.05
    if p_val < alpha:
        print(f"Result: Reject the Null Hypothesis (H0) at alpha={alpha}.")
        print("Conclusion: There is a statistically significant difference in calculated average speeds. Tampered vehicles exhibit highly anomalous, artificially low speed ratios (p < 0.05).")
    else:
        print("Result: Fail to reject the Null Hypothesis (H0). No statistically significant speed differences found.")

if __name__ == "__main__":
    perform_eda()
