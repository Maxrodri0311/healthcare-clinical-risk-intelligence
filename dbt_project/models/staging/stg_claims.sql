-- Staging model for Financial & Operational Claim Transactions
with raw_source as (
    select * from read_parquet('data/raw_oncology_claims.parquet')
)

select
    claim_hash,
    patient_id,
    cast(treatment_date as date) as claim_service_date,
    date_trunc('month', cast(treatment_date as date)) as billing_cycle_month,
    cast(claim_amount_usd as decimal(12, 2)) as allowed_claim_amount_usd,
    case
        when claim_amount_usd >= 50000.0 then 'HIGH_SEVERITY_TIER'
        when claim_amount_usd >= 20000.0 then 'MODERATE_TIER'
        else 'STANDARD_AMBULATORY_TIER'
    end as claim_severity_bucket,
    cast(readmission_30d as integer) as is_readmission_30d_incident
from raw_source
