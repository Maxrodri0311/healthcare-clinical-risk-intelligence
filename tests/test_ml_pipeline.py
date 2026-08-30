import pytest
import os
import pandas as pd
from src.data_generator import generate_oncology_dataset
from src.dbt_runner import DuckDBDbtRunner
from src.ml_tournament import OncologyMLTournament

@pytest.fixture(scope="module")
def prepared_fact_table(tmp_path_factory):
    raw_fn = tmp_path_factory.mktemp("raw") / "raw.parquet"
    df = generate_oncology_dataset(num_records=2000, random_seed=42)
    df.to_parquet(str(raw_fn), index=False)
    
    runner = DuckDBDbtRunner()
    df_fact = runner.execute_transformations(raw_parquet_path=str(raw_fn))
    
    fact_fn = tmp_path_factory.mktemp("curated") / "fact.parquet"
    df_fact.to_parquet(str(fact_fn), index=False)
    return str(fact_fn)

def test_ml_tournament_and_cost_optimization(prepared_fact_table):
    tournament = OncologyMLTournament()
    results = tournament.run_tournament(parquet_path=prepared_fact_table)
    
    assert "Logistic_Regression" in results
    assert "XGBoost" in results
    assert "LightGBM" in results
    assert "Cost_Optimization" in results
    
    # Check AUC validity
    best_auc = max(results["XGBoost"]["auc_roc"], results["LightGBM"]["auc_roc"])
    assert best_auc > 0.60
    assert results["Cost_Optimization"]["optimal_threshold"] > 0
    assert results["Cost_Optimization"]["projected_annual_savings_millions"] > 0
