-- Staging model for Clinical Oncology Treatments & Radiation Dosages
with raw_source as (
    select * from read_parquet('data/raw_oncology_claims.parquet')
)

select
    claim_hash,
    patient_id,
    trim(cancer_type) as primary_oncology_diagnosis,
    trim(cancer_stage) as clinical_cancer_stage,
    cast(total_dose_gy as float) as radiation_total_dose_gy,
    cast(fractions_count as integer) as radiation_fractions_count,
    cast(concurrent_chemo as integer) as has_concurrent_chemotherapy,
    cast(prior_hospitalizations as integer) as prior_hospitalization_count,
    round(cast(total_dose_gy as float) / nullif(cast(fractions_count as float), 0), 2) as avg_dose_per_fraction_gy
from raw_source
