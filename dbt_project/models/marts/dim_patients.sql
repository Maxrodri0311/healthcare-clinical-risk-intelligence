-- Dimension Model: Patient Demographics & Risk Profile
with stg_p as (
    select * from {{ ref('stg_patients') }}
)

select
    patient_id,
    patient_age,
    patient_gender,
    insurance_payer_tier,
    is_geriatric_cohort,
    baseline_charlson_index,
    case
        when baseline_charlson_index >= 4 then 'VERY_HIGH_COMORBIDITY'
        when baseline_charlson_index >= 2 then 'MODERATE_COMORBIDITY'
        else 'LOW_COMORBIDITY'
    end as comorbidity_risk_tier
from stg_p
