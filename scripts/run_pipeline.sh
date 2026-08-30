#!/usr/bin/env bash
set -euo pipefail

echo "================================================================"
echo " [RHI Radion Health] Running End-to-End Oncology ML Pipeline   "
echo "================================================================"

# 1. Generate 50,000+ synthetic clinical records
echo "[1/4] Generating 50,000+ radiation oncology claims..."
python src/data_generator.py

# 2. Run dbt Dimensional Transformations
echo "[2/4] Materializing dbt Star Schema models in DuckDB..."
python src/dbt_runner.py

# 3. Train XGBoost vs LightGBM Tournament & Cost Calibration
echo "[3/4] Running Dual Gradient Boosting Tournament..."
python src/ml_tournament.py

# 4. Execute AI Fairness & Demographic Parity Audit
echo "[4/4] Auditing HHS Section 1557 / NYC Law 144 AI Fairness..."
python src/fairness_audit.py

echo "================================================================"
echo " [SUCCESS] Pipeline execution complete. Artifacts ready in web/ "
echo "================================================================"
