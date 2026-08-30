-- Fact Model: Unified Oncology Claims, Dosages & Readmission Incident Fact Table
with claims as (
    select * from {{ ref('stg_claims') }}
),
treatments as (
    select * from {{ ref('stg_treatments') }}
),
patients as (
    select * from {{ ref('dim_patients') }}
)

select
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
from claims c
inner join treatments t on c.claim_hash = t.claim_hash
inner join patients p on c.patient_id = p.patient_id
