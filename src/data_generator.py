"""
RHI Radion Health, Inc. - Synthetic Oncology Telemetry & Claims Generator
Generates 50,000+ realistic radiation oncology treatment & claim records with clinical noise.
"""
import os
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_oncology_dataset(num_records: int = 50000, random_seed: int = 42) -> pd.DataFrame:
    np.random.seed(random_seed)
    print(f"[*] Generating {num_records:,} Radiation Oncology Claims for RHI Radion Health...")

    patient_ids = [f"PAT-{i:06d}" for i in range(1, num_records + 1)]
    ages = np.random.normal(loc=64, scale=11, size=num_records).clip(28, 92).astype(int)
    genders = np.random.choice(["Female", "Male", "Non-Binary"], size=num_records, p=[0.52, 0.46, 0.02])
    
    insurance_types = np.random.choice(
        ["Medicare Advantage", "Commercial PPO", "Medicaid Managed", "Commercial HMO"], 
        size=num_records, 
        p=[0.48, 0.28, 0.14, 0.10]
    )

    cancer_types = np.random.choice(
        ["Breast (C50)", "Lung (C34)", "Prostate (C61)", "Colorectal (C18)", "Head & Neck (C76)"],
        size=num_records,
        p=[0.30, 0.24, 0.22, 0.14, 0.10]
    )

    cancer_stages = np.random.choice(["Stage I", "Stage II", "Stage III", "Stage IV"], size=num_records, p=[0.25, 0.35, 0.25, 0.15])
    charlson_index = np.random.poisson(lam=1.8, size=num_records).clip(0, 8)
    
    # Radiation protocol parameters
    total_dose_gy = np.random.uniform(25.0, 78.0, size=num_records).round(1)
    fractions_count = (total_dose_gy / np.random.uniform(1.8, 2.5, size=num_records)).astype(int).clip(5, 40)
    concurrent_chemo = np.random.choice([0, 1], size=num_records, p=[0.62, 0.38])
    prior_hospitalizations = np.random.poisson(lam=0.6, size=num_records).clip(0, 6)

    # Base dates across 2025-2026
    start_date = datetime(2025, 1, 1)
    random_days = np.random.randint(0, 500, size=num_records)
    treatment_dates = [start_date + timedelta(days=int(d)) for d in random_days]

    # Costs: Gamma distribution based on complexity
    base_cost = np.random.gamma(shape=3.5, scale=4500, size=num_records)
    stage_multiplier = np.where(cancer_stages == "Stage IV", 2.2, np.where(cancer_stages == "Stage III", 1.6, 1.0))
    claim_amount = (base_cost * stage_multiplier + (total_dose_gy * 120) + (charlson_index * 850)).round(2)

    # Clinical readmission probability logit
    stage_weight = np.where(cancer_stages == "Stage IV", 1.2, np.where(cancer_stages == "Stage III", 0.7, 0.0))
    logit = (
        -3.2
        + 0.025 * (ages - 60)
        + 0.35 * charlson_index
        + 0.02 * (total_dose_gy - 45)
        + 0.55 * concurrent_chemo
        + 0.45 * prior_hospitalizations
        + stage_weight
        + np.random.normal(0, 0.25, size=num_records) # Clinical noise
    )
    readmission_prob = 1.0 / (1.0 + np.exp(-logit))
    readmission_30d = (np.random.rand(num_records) < readmission_prob).astype(int)

    # Generate SHA-256 Claim Hash for Idempotence
    claim_hashes = [
        hashlib.sha256(f"{pid}_{dt.strftime('%Y%m%d')}_{dose}".encode()).hexdigest()[:16]
        for pid, dt, dose in zip(patient_ids, treatment_dates, total_dose_gy)
    ]

    df = pd.DataFrame({
        "claim_hash": claim_hashes,
        "patient_id": patient_ids,
        "age": ages,
        "gender": genders,
        "insurance_type": insurance_types,
        "cancer_type": cancer_types,
        "cancer_stage": cancer_stages,
        "charlson_comorbidity_index": charlson_index,
        "total_dose_gy": total_dose_gy,
        "fractions_count": fractions_count,
        "concurrent_chemo": concurrent_chemo,
        "prior_hospitalizations": prior_hospitalizations,
        "treatment_date": [dt.strftime("%Y-%m-%d") for dt in treatment_dates],
        "claim_amount_usd": claim_amount,
        "readmission_30d": readmission_30d
    })

    os.makedirs("data", exist_ok=True)
    parquet_path = "data/raw_oncology_claims.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"[+] Successfully exported {len(df):,} records to {parquet_path}")
    print(f"[+] Readmission baseline rate: {df['readmission_30d'].mean():.2%}")
    print(f"[+] Total Ingested Claims: ${df['claim_amount_usd'].sum():,.2f} USD")
    return df

if __name__ == "__main__":
    generate_oncology_dataset(50000)