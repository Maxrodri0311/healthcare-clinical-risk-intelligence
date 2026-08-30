#!/usr/bin/env bash
set -euo pipefail

echo "================================================================"
echo " [RHI Radion Health] Bootstrapping Oncology Analytics Lakehouse"
echo "================================================================"

# 1. Ensure Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Setup directory hierarchy
mkdir -p data/raw data/curated data/marts web dbt_project/models/staging dbt_project/models/marts

echo "[+] Directory structure initialized."
echo "[+] Environment ready for pipeline execution."
