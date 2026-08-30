-- Dimension Model: Clinical Oncology Protocols & Radiation Classification
with stg_t as (
    select * from {{ ref('stg_treatments') }}
)

select
    distinct
    primary_oncology_diagnosis,
    clinical_cancer_stage,
    case
        when radiation_total_dose_gy >= 60.0 then 'HYPER_FRACTIONATED_INTENSIVE'
        when radiation_total_dose_gy >= 45.0 then 'STANDARD_CURATIVE'
        else 'PALLIATIVE_HYPOFRACTIONATED'
    end as radiation_protocol_category,
    has_concurrent_chemotherapy
from stg_t
