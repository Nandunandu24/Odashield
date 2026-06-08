import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
import xgboost as xgb

def train_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", "models", "ecu_training_data.csv")
    model_dir = os.path.join(current_dir, "..", "models")
    model_path = os.path.join(model_dir, "xgboost_fraud_model.json")
    
    # Check if dataset exists, if not generate it
    if not os.path.exists(data_path):
        print("Dataset not found. Generating synthetic dataset first...")
        from backend.scripts.generate_ecu_data import generate_synthetic_data
        generate_synthetic_data(data_path)
        
    print(f"Loading training data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Define features and label
    features = [
        "reported_odometer", "ecu_ecm", "ecu_tcm", "ecu_abs", 
        "ecu_airbag", "ecu_cluster", "engine_hours", "max_variance", 
        "avg_speed"
    ]
    
    X = df[features]
    y = df["is_tampered"]
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set shape: {X_train.shape}, Test set shape: {X_test.shape}")
    
    # Define and train XGBoost classifier
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss"
    )
    
    print("Training XGBoost Classifier...")
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    auc_roc = roc_auc_score(y_test, y_proba)
    
    print("\n--- Model Evaluation Results ---")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"AUC-ROC: {auc_roc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model
    os.makedirs(model_dir, exist_ok=True)
    model.save_model(model_path)
    print(f"Successfully saved XGBoost model to {model_path}")

if __name__ == "__main__":
    train_model()
