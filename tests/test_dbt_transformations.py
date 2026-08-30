import pytest
import os
import pandas as pd
from src.data_generator import generate_oncology_dataset
from src.dbt_runner import DuckDBDbtRunner

@pytest.fixture(scope="module")
def sample_dataset(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "sample_claims.parquet"
    df = generate_oncology_dataset(num_records=1500, random_seed=42)
    df.to_parquet(str(fn), index=False)
    return str(fn)

def test_duckdb_dbt_star_schema(sample_dataset):
    runner = DuckDBDbtRunner()
    df_fact = runner.execute_transformations(raw_parquet_path=sample_dataset)
    
    assert len(df_fact) == 1500
    assert "comorbidity_risk_tier" in df_fact.columns
    assert "claim_severity_bucket" in df_fact.columns
    assert "is_readmission_30d_incident" in df_fact.columns
    
    # Check KPIs
    kpis = runner.query_kpis()
    assert kpis["total_episodes"] == 1500
    assert kpis["readmission_rate_pct"] > 0
    assert kpis["avg_claim_cost_usd"] > 1000
