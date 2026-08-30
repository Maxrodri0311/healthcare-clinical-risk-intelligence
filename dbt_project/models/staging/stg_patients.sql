-- Staging model for Patient Demographics & Baseline Health
with raw_source as (
    select * from read_parquet('data/raw_oncology_claims.parquet')
)

select
    distinct
    patient_id,
    cast(age as integer) as patient_age,
    trim(gender) as patient_gender,
    trim(insurance_type) as insurance_payer_tier,
    case 
        when age >= 65 then true 
        else false 
    end as is_geriatric_cohort,
    cast(charlson_comorbidity_index as integer) as baseline_charlson_index
from raw_source
