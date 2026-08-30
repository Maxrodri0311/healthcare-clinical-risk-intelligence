import pytest
import os
import pandas as pd
from src.data_generator import generate_oncology_dataset

def test_data_generation_dimensions():
    df = generate_oncology_dataset(num_records=1000, random_seed=99)
    assert len(df) == 1000
    assert "claim_hash" in df.columns
    assert "patient_id" in df.columns
    assert "charlson_comorbidity_index" in df.columns
    assert "total_dose_gy" in df.columns
    assert "readmission_30d" in df.columns

def test_clinical_distributions():
    df = generate_oncology_dataset(num_records=2000, random_seed=99)
    # Check age range
    assert df["age"].min() >= 18
    assert df["age"].max() <= 100
    # Check binary readmission flag
    assert set(df["readmission_30d"].unique()).issubset({0, 1})
    # Check positive claim cost
    assert (df["claim_amount_usd"] > 0).all()
    # Check hash uniqueness
    assert df["claim_hash"].nunique() == 2000
