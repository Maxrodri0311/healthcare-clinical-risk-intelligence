"""
RHI Healthcare Clinical Practice, Inc. - Clinical AI Algorithmic Fairness & Bias Auditor
Evaluates compliance with HHS Section 1557 and NYC Local Law 144 (Four-Fifths / 80% Rule).
"""
import json
import os
import numpy as np
import pandas as pd
from typing import Dict, Any

class ClinicalFairnessAuditor:
    def __init__(self, threshold_ratio: float = 0.80):
        self.threshold_ratio = threshold_ratio  # EEOC / HHS 80% Rule (Four-Fifths)

    def audit_demographic_parity(self, parquet_path: str = "data/curated_fact_table.parquet") -> Dict[str, Any]:
        print("[*] Auditing Algorithmic Fairness & Disparate Impact for RHI Healthcare Analytics...")
        df = pd.read_parquet(parquet_path)

        audit_results = {
            "regulation_standards": ["HHS Section 1557", "NYC Local Law 144", "EEOC Uniform Guidelines"],
            "disparate_impact_threshold": self.threshold_ratio,
            "demographic_evaluations": {}
        }

        # 1. Audit Gender Parity
        audit_results["demographic_evaluations"]["gender"] = self._evaluate_attribute(
            df, sensitive_col="patient_gender", target_col="is_readmission_30d_incident"
        )

        # 2. Audit Age / Geriatric Parity (<65 vs >=65)
        df["age_cohort"] = np.where(df["patient_age"] >= 65, "Senior (65+)", "Adult (<65)")
        audit_results["demographic_evaluations"]["age_cohort"] = self._evaluate_attribute(
            df, sensitive_col="age_cohort", target_col="is_readmission_30d_incident"
        )

        # 3. Audit Insurance Payer Parity
        audit_results["demographic_evaluations"]["insurance_payer"] = self._evaluate_attribute(
            df, sensitive_col="insurance_payer_tier", target_col="is_readmission_30d_incident"
        )

        # Overall Status
        all_passed = all(
            ev["compliance_status"] == "COMPLIANT" 
            for ev in audit_results["demographic_evaluations"].values()
        )
        audit_results["overall_compliance"] = "CERTIFIED_FAIR" if all_passed else "FLAGGED_FOR_REVIEW"

        os.makedirs("web/data", exist_ok=True)
        with open("web/data/fairness_audit.json", "w") as f:
            json.dump(audit_results, f, indent=2)

        print(f"[+] AI Fairness Audit Complete. Compliance Status: {audit_results['overall_compliance']}")
        return audit_results

    def _evaluate_attribute(self, df: pd.DataFrame, sensitive_col: str, target_col: str) -> Dict[str, Any]:
        groups = df.groupby(sensitive_col)[target_col].agg(
            total_count="count",
            flagged_count="sum",
            positive_rate="mean"
        ).reset_index()

        # EEOC standard: Only evaluate groups with sufficient statistical power (>= 2% of sample or >= 30 records)
        min_sample = max(30, int(len(df) * 0.02))
        stat_powered = groups[groups["total_count"] >= min_sample]
        if len(stat_powered) == 0:
            stat_powered = groups

        max_rate = stat_powered["positive_rate"].max()
        groups["disparate_impact_ratio"] = groups["positive_rate"] / max_rate if max_rate > 0 else 1.0

        min_ratio = stat_powered["positive_rate"].min() / max_rate if max_rate > 0 else 1.0
        is_compliant = min_ratio >= self.threshold_ratio

        return {
            "attribute_name": sensitive_col,
            "min_disparate_impact_ratio": round(float(min_ratio), 4),
            "compliance_status": "COMPLIANT" if is_compliant else "NON_COMPLIANT_DISPARITY",
            "group_breakdown": [
                {
                    "group": str(row[sensitive_col]),
                    "sample_size": int(row["total_count"]),
                    "flagged_episodes": int(row["flagged_count"]),
                    "selection_rate": round(float(row["positive_rate"]), 4),
                    "disparate_impact_ratio": round(float(row["disparate_impact_ratio"]), 4)
                }
                for _, row in groups.iterrows()
            ]
        }

if __name__ == "__main__":
    auditor = ClinicalFairnessAuditor()
    auditor.audit_demographic_parity()
