# 🛡️ OdoShield: Used Car Fraud Auditor & Odometer Fraud Detector

[![Deployed Link](https://img.shields.io/badge/Deployed%20App-Render-blueviolet?style=for-the-badge&logo=render)](https://odashield.onrender.com/)
[![License](https://img.shields.io/badge/License-Private-red?style=for-the-badge)](#)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Express.js](https://img.shields.io/badge/Express.js-4.19%2B-lightgrey?style=for-the-badge&logo=express)](https://expressjs.com/)

OdoShield is an advanced **6-Layer Used Car Fraud Auditor** and valuation validation system. Built with a high-performance **FastAPI backend** and a futuristic **cyberpunk-themed frontend**, OdoShield aggregates vehicle registry timelines, ECU data, machine learning probabilities, computer vision assessments, and generative AI summaries to expose hidden mileage tampering and fraud.

### 🌐 Live Production Link
The application is deployed and available at: **[https://odashield.onrender.com/](https://odashield.onrender.com/)**

---

## 🚀 The 6-Layer Verification Architecture

OdoShield doesn't just look at a number; it audits the car's history, software, hardware, and physical condition through six independent verification gates:

```
[ Form Submission ] ──> 🛡️ OdoShield Engine 
                          │
                          ├──> Layer 1: VAHAN Registry Historical Analysis (Timeline Anomaly)
                          ├──> Layer 2: ECU Module Consistency Check (Variance & Speed Audit)
                          ├──> Layer 3: XGBoost Classifier Model (Machine Learning Probability)
                          ├──> Layer 4: PyTorch CNN Wear Classifier (Physical Image Scan)
                          ├──> Layer 5: Hugging Face LLM Report Generator (Natural Language Analysis)
                          └──> Layer 6: Weighted Fraud Score Aggregator (Final Recommendation)
```

### 1. Registry History Audit (Layer 1)
Parses regional registry timelines (VAHAN) to identify odometer regressions (e.g., mileage going down between ownership transfers or service checks).

### 2. ECU Module Audit (Layer 2)
Extracts and compares internal odometer readings stored in separate vehicle ECUs:
* Engine Control Module (**ECM**)
* Transmission Control Module (**TCM**)
* Anti-lock Braking System (**ABS**)
* Airbag Module
* Instrument Cluster (**CLUSTER**)
Checks for mileage variances across modules and flags extreme average speeds relative to engine hours.

### 3. Machine Learning Fraud Probability (Layer 3)
Uses an **XGBoost Classifier Model** trained on historical tampering patterns. It calculates fraud probability based on variables such as engine hours, max module variance, and calculated average speed, with a robust heuristic fallback algorithm if ML libraries are offline.

### 4. Physical Wear CNN Classifier (Layer 4)
Uses a **PyTorch Convolutional Neural Network (CNN)** to inspect uploaded pictures of high-wear areas (pedals, steering wheel, seats) and classifies physical wear into `LOW`, `MEDIUM`, or `HIGH`, correlating it against reported mileage.

### 5. AI-Powered Forensic Report (Layer 5)
Leverages the **Hugging Face Serverless Inference API** (running `meta-llama/Meta-Llama-3-8B-Instruct`) to generate a detailed, readable vehicle inspection report. A dynamic template generator serves as a local fallback when the API token is not configured.

### 6. Weighted Score Aggregation (Layer 6)
Aggregates all layer outputs into a final consolidated **Fraud Risk Score**, risk categorization (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and action recommendation (`ACCEPT`, `REVIEW`, `REJECT`).

---

## ⚡ Additional Core Engines

### 💰 Damage & Fair Value Valuation Engine
Calibrates the fair market worth of the vehicle based on:
* Asking Price and base model values.
* Aggregated Fraud Risk.
* Component Wear level.
* Paint Thickness checks (identifying repainted panels).
* Structural/Cosmetic condition (dents, scratches).

### 📄 Insurance History Audit Logs
Exposes vehicle health history by checking:
* Active policy validation and expiry timelines.
* Historical insurance claims count & total claim payouts.
* No Claim Bonus (NCB) reset tracking.

---

## 🎨 Premium Frontend Design

* **Futuristic Cyberpunk UI**: High-fidelity neon dashboard built with raw HTML, Javascript, and Vanilla CSS.
* **Dual View Layout**: Toggle seamlessly between desktop (laptop) view and scaled mobile interfaces.
* **2x2 Grid Visualization**: Simultaneous grid displaying all 4 audit components without overlapping.
* **Diagnostic Streaming Terminal**: Real-time mock diagnostic feed streaming active check logs on form submission.
* **High Contrast PDF Export**: One-click, styled PDF forensic report downloads.

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── config.py           # Settings and Environment Configuration
│   │   ├── database.py         # SQLAlchemy & SQLite/Postgres Engines
│   │   ├── main.py             # FastAPI App, Routes, & Mounting
│   │   └── services/           # Individual Audit Logic Engines
│   │       ├── ecu.py
│   │       ├── llm_report.py
│   │       ├── score_aggregator.py
│   │       ├── vahan.py
│   │       ├── valuation.py
│   │       ├── wear_cnn.py
│   │       └── xgboost_model.py
│   └── tests/                  # Pytest automated test scripts
│       ├── test_audit.py
│       ├── test_edge_cases.py
│       └── test_valuation.py
├── frontend/                   # React/Vite/Alternative Frontend workspace
├── public/                     # Main Cyberpunk Web Frontend
│   ├── app.js                  # Frontend logic & API request handler
│   ├── index.html              # Main HTML Structure
│   └── styles.css              # Cyberpunk Design System & Layouts
├── server.js                   # Node.js/Express App Proxy
├── docker-compose.yml          # Container configuration
└── package.json                # Express server dependencies
```

---

## 🛠️ Installation & Local Setup

### Prerequisites
* Python 3.10+
* Node.js 18+

### 1. Set Up Environment Variables
Create a `.env` file in the root directory:
```env
# Database Settings (optional - falls back to SQLite locally)
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/odoshield

# Hugging Face API key for AI Forensic Report (optional)
HF_API_KEY=your_hugging_face_api_key
HF_MODEL_ID=meta-llama/Meta-Llama-3-8B-Instruct
```

### 2. Backend Installation (FastAPI)
Navigate to the root directory and install dependencies:
```bash
pip install -r backend/requirements.txt
```

Run the FastAPI backend:
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
The interactive API documentation will be available at: `http://127.0.0.1:8000/docs`

### 3. Frontend Installation (Express Node Proxy)
Install node dependencies:
```bash
npm install
```

Run the Node.js server:
```bash
npm start
```
The application will run at: `http://localhost:3000`

*(Note: The FastAPI server also mounts and serves the static frontend at `http://127.0.0.1:8000/` automatically).*

---

## 🧪 Running Automated Tests

OdoShield has a robust automated test suite testing the audit engines, valuation calculations, and edge cases. To run the tests, execute:

```bash
python -m pytest backend/tests
```

---

## 🚀 Deployed on Render

OdoShield is deployed using a single service environment on Render:
1. **Web Service**: Powered by FastAPI directly or via the Node Express server.
2. **Database**: Render PostgreSQL database.
3. **Link**: [https://odashield.onrender.com/](https://odashield.onrender.com/)

---

## 📄 License
This project is proprietary and confidential. All rights reserved.
