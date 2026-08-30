import pytest
import os
import pandas as pd
from src.data_generator import generate_oncology_dataset
from src.dbt_runner import DuckDBDbtRunner
from src.fairness_audit import ClinicalFairnessAuditor

@pytest.fixture(scope="module")
def fact_table_fixture(tmp_path_factory):
    raw_fn = tmp_path_factory.mktemp("raw") / "raw.parquet"
    df = generate_oncology_dataset(num_records=2000, random_seed=42)
    df.to_parquet(str(raw_fn), index=False)
    
    runner = DuckDBDbtRunner()
    df_fact = runner.execute_transformations(raw_parquet_path=str(raw_fn))
    
    fact_fn = tmp_path_factory.mktemp("curated") / "fact.parquet"
    df_fact.to_parquet(str(fact_fn), index=False)
    return str(fact_fn)

def test_algorithmic_fairness_audit(fact_table_fixture):
    auditor = ClinicalFairnessAuditor(threshold_ratio=0.75)
    audit = auditor.audit_demographic_parity(parquet_path=fact_table_fixture)
    
    assert "demographic_evaluations" in audit
    assert "gender" in audit["demographic_evaluations"]
    assert "age_cohort" in audit["demographic_evaluations"]
    assert "insurance_payer" in audit["demographic_evaluations"]
    
    gender_eval = audit["demographic_evaluations"]["gender"]
    assert gender_eval["min_disparate_impact_ratio"] > 0.60
