"""
RHI Healthcare Clinical Practice, Inc. - DuckDB In-Memory dbt Transformation Runner
Executes dimensional modeling and materializes the Star Schema Lakehouse.
"""
import os
import duckdb
import pandas as pd
from typing import Dict, Any

class DuckDBDbtRunner:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.con = duckdb.connect(db_path)

    def execute_transformations(self, raw_parquet_path: str = "data/raw_oncology_claims.parquet") -> pd.DataFrame:
        print(f"[*] Initializing DuckDB In-Memory OLAP Engine from {raw_parquet_path}...")
        
        # 1. Staging Views
        self.con.execute(f"""
            CREATE OR REPLACE VIEW stg_patients AS
            SELECT DISTINCT
                patient_id,
                CAST(age AS INTEGER) as patient_age,
                TRIM(gender) as patient_gender,
                TRIM(insurance_type) as insurance_payer_tier,
                CASE WHEN age >= 65 THEN true ELSE false END as is_geriatric_cohort,
                CAST(charlson_comorbidity_index AS INTEGER) as baseline_charlson_index
            FROM read_parquet('{raw_parquet_path}');
        """)

        self.con.execute(f"""
            CREATE OR REPLACE VIEW stg_claims AS
            SELECT
                claim_hash,
                patient_id,
                CAST(treatment_date AS DATE) as claim_service_date,
                DATE_TRUNC('month', CAST(treatment_date AS DATE)) as billing_cycle_month,
                CAST(claim_amount_usd AS DECIMAL(12, 2)) as allowed_claim_amount_usd,
                CASE
                    WHEN claim_amount_usd >= 50000.0 THEN 'HIGH_SEVERITY_TIER'
                    WHEN claim_amount_usd >= 20000.0 THEN 'MODERATE_TIER'
                    ELSE 'STANDARD_AMBULATORY_TIER'
                END as claim_severity_bucket,
                CAST(readmission_30d AS INTEGER) as is_readmission_30d_incident
            FROM read_parquet('{raw_parquet_path}');
        """)

        self.con.execute(f"""
            CREATE OR REPLACE VIEW stg_treatments AS
            SELECT
                claim_hash,
                patient_id,
                TRIM(cancer_type) as primary_oncology_diagnosis,
                TRIM(cancer_stage) as clinical_cancer_stage,
                CAST(total_dose_gy AS FLOAT) as radiation_total_dose_gy,
                CAST(fractions_count AS INTEGER) as radiation_fractions_count,
                CAST(concurrent_chemo AS INTEGER) as has_concurrent_chemotherapy,
                CAST(prior_hospitalizations AS INTEGER) as prior_hospitalization_count,
                ROUND(CAST(total_dose_gy AS FLOAT) / NULLIF(CAST(fractions_count AS FLOAT), 0), 2) as avg_dose_per_fraction_gy
            FROM read_parquet('{raw_parquet_path}');
        """)

        # 2. Dimensional Tables
        self.con.execute("""
            CREATE OR REPLACE TABLE dim_patients AS
            SELECT
                patient_id,
                patient_age,
                patient_gender,
                insurance_payer_tier,
                is_geriatric_cohort,
                baseline_charlson_index,
                CASE
                    WHEN baseline_charlson_index >= 4 THEN 'VERY_HIGH_COMORBIDITY'
                    WHEN baseline_charlson_index >= 2 THEN 'MODERATE_COMORBIDITY'
                    ELSE 'LOW_COMORBIDITY'
                END as comorbidity_risk_tier
            FROM stg_patients;
        """)

        # 3. Fact Table Materialization
        self.con.execute("""
            CREATE OR REPLACE TABLE fct_oncology_admissions AS
            SELECT
                c.claim_hash,
                c.patient_id,
                c.claim_service_date,
                c.billing_cycle_month,
                p.patient_age,
                p.patient_gender,
                p.insurance_payer_tier,
                p.baseline_charlson_index,
                p.comorbidity_risk_tier,
                t.primary_oncology_diagnosis,
                t.clinical_cancer_stage,
                t.radiation_total_dose_gy,
                t.radiation_fractions_count,
                t.has_concurrent_chemotherapy,
                t.prior_hospitalization_count,
                t.avg_dose_per_fraction_gy,
                c.allowed_claim_amount_usd,
                c.claim_severity_bucket,
                c.is_readmission_30d_incident
            FROM stg_claims c
            INNER JOIN stg_treatments t ON c.claim_hash = t.claim_hash
            INNER JOIN dim_patients p ON c.patient_id = p.patient_id;
        """)

        df_fact = self.con.execute("SELECT * FROM fct_oncology_admissions").df()
        out_path = "data/curated_fact_table.parquet"
        df_fact.to_parquet(out_path, index=False)
        print(f"[+] Materialized Star Schema Fact Table with {len(df_fact):,} rows to {out_path}")
        return df_fact

    def query_kpis(self) -> Dict[str, Any]:
        """Calculates executive clinical & financial KPIs in sub-10ms."""
        query = """
            SELECT 
                COUNT(*) as total_episodes,
                ROUND(AVG(is_readmission_30d_incident) * 100, 2) as readmission_rate_pct,
                ROUND(SUM(allowed_claim_amount_usd) / 1000000, 2) as total_spend_millions,
                ROUND(AVG(allowed_claim_amount_usd), 2) as avg_claim_cost_usd,
                ROUND(AVG(radiation_total_dose_gy), 1) as avg_radiation_dose_gy
            FROM fct_oncology_admissions;
        """
        result = self.con.execute(query).df().to_dict(orient="records")[0]
        return result

if __name__ == "__main__":
    runner = DuckDBDbtRunner()
    runner.execute_transformations()
    kpis = runner.query_kpis()
    print("[+] Executive KPIs:", kpis)
