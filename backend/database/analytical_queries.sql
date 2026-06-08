-- =====================================================================
-- OdoShield Advanced Fleet Analytics Queries (Data Analyst Portfolio)
-- =====================================================================

-- ---------------------------------------------------------------------
-- QUERY 1: Odometer Fraud Rate by Vehicle Manufacturer & Model
-- Demonstrates: CTEs, Grouping, Aggregations, Case statements, and percentages.
-- ---------------------------------------------------------------------
WITH vehicle_risk_groups AS (
    SELECT 
        v.make,
        v.model,
        f.risk_level,
        CASE WHEN f.risk_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END as is_fraudulent
    FROM vehicles v
    JOIN fraud_scores f ON v.vehicle_id = f.vehicle_id
)
SELECT 
    make,
    model,
    COUNT(*) as total_inspected,
    SUM(is_fraudulent) as fraud_cases,
    ROUND((SUM(is_fraudulent)::decimal / COUNT(*)) * 100, 2) as fraud_rate_percentage,
    SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_cases
FROM vehicle_risk_groups
GROUP BY make, model
HAVING COUNT(*) >= 5 -- Only show models with significant sample size
ORDER BY fraud_rate_percentage DESC, total_inspected DESC;


-- ---------------------------------------------------------------------
-- QUERY 2: Correlation Analysis - Ownership Transfers vs Fraud Rates
-- Demonstrates: Subqueries, grouping by discrete segments, and statistical categorization.
-- ---------------------------------------------------------------------
SELECT 
    current_owner as owner_number,
    COUNT(*) as total_inspected,
    SUM(CASE WHEN risk_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) as fraud_cases,
    ROUND(
        (SUM(CASE WHEN risk_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END)::decimal / COUNT(*)) * 100, 
        2
    ) as fraud_rate_percentage
FROM vehicles v
JOIN fraud_scores f ON v.vehicle_id = f.vehicle_id
GROUP BY current_owner
ORDER BY owner_number ASC;


-- ---------------------------------------------------------------------
-- QUERY 3: Running Average of Fraud Probability by Registration City Over Time
-- Demonstrates: Window functions (PARTITION BY, ORDER BY, ROWS BETWEEN).
-- ---------------------------------------------------------------------
SELECT 
    v.registration_city,
    f.assessed_at::date as assessment_date,
    v.make,
    f.fraud_probability,
    ROUND(
        AVG(f.fraud_probability) OVER(
            PARTITION BY v.registration_city 
            ORDER BY f.assessed_at 
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        )::decimal, 
        2
    ) as rolling_average_fraud_prob_city
FROM vehicles v
JOIN fraud_scores f ON v.vehicle_id = f.vehicle_id
ORDER BY v.registration_city, f.assessed_at;


-- ---------------------------------------------------------------------
-- QUERY 4: SQL Odometer Rollback Detection (Self-Join Verification)
-- Demonstrates: Self-joins, row numbering, and finding temporal anomalies in SQL.
-- ---------------------------------------------------------------------
WITH ordered_vahan_records AS (
    SELECT 
        vehicle_id,
        recorded_date,
        odometer_reading,
        ROW_NUMBER() OVER(PARTITION BY vehicle_id ORDER BY recorded_date ASC) as seq
    FROM vaahan_records
)
SELECT 
    v.vin,
    v.make,
    v.model,
    prev_rec.recorded_date as original_date,
    prev_rec.odometer_reading as original_odometer,
    curr_rec.recorded_date as rollback_detected_date,
    curr_rec.odometer_reading as rolledback_odometer,
    (prev_rec.odometer_reading - curr_rec.odometer_reading) as odometer_drop_km
FROM ordered_vahan_records curr_rec
JOIN ordered_vahan_records prev_rec 
    ON curr_rec.vehicle_id = prev_rec.vehicle_id 
    AND curr_rec.seq = prev_rec.seq + 1
JOIN vehicles v ON v.vehicle_id = curr_rec.vehicle_id
WHERE curr_rec.odometer_reading < prev_rec.odometer_reading
ORDER BY odometer_drop_km DESC;
