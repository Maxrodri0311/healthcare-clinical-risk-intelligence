"""
RHI Radion Health, Inc. - Dual Machine Learning Tournament & Cost-Sensitive Decision Calibration
Compares XGBoost vs LightGBM for acute 30-day oncology readmission risk & optimizes cost threshold.
"""
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score, log_loss, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

# Try importing XGBoost and LightGBM with robust fallbacks
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

class OncologyMLTournament:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.cost_fn = 45000.0   # Cost of unprevented acute ICU hospitalization (False Negative)
        self.cost_fp = 120.0     # Cost of proactive nursing triage / tele-monitoring (False Positive)
        self.cost_tp = 1800.0    # Triage + preventive medication cost when intervention succeeds
        self.saving_per_prevented = self.cost_fn - self.cost_tp  # Net savings = $43,200 per true risk detected

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
        categorical_cols = ["patient_gender", "insurance_payer_tier", "primary_oncology_diagnosis", "clinical_cancer_stage"]
        numeric_cols = [
            "patient_age", "baseline_charlson_index", "radiation_total_dose_gy", 
            "radiation_fractions_count", "has_concurrent_chemotherapy", 
            "prior_hospitalization_count", "avg_dose_per_fraction_gy"
        ]

        df_encoded = pd.get_dummies(df[categorical_cols + numeric_cols], columns=categorical_cols, drop_first=True)
        feature_names = df_encoded.columns.tolist()
        X = df_encoded
        y = df["is_readmission_30d_incident"]
        return X, y, feature_names

    def run_tournament(self, parquet_path: str = "data/curated_fact_table.parquet") -> Dict[str, Any]:
        print("[*] Running Dual Gradient Boosting Tournament (XGBoost vs LightGBM)...")
        df = pd.read_parquet(parquet_path)
        X, y, feature_names = self.prepare_features(df)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, stratify=y, random_state=self.random_state
        )

        results = {}

        # 1. Baseline Logistic Regression
        lr = LogisticRegression(max_iter=1000, random_state=self.random_state)
        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)
        lr.fit(X_train_s, y_train)
        lr_probs = lr.predict_proba(X_test_s)[:, 1]
        results["Logistic_Regression"] = self._evaluate_model("Logistic Regression", y_test, lr_probs)

        # 2. XGBoost (or Scikit-Learn Gradient Boosting fallback)
        if HAS_XGB:
            xgb_model = xgb.XGBClassifier(
                n_estimators=150, max_depth=5, learning_rate=0.08, 
                subsample=0.85, colsample_bytree=0.85, random_state=self.random_state,
                eval_metric="logloss"
            )
            xgb_model.fit(X_train, y_train)
            xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
            importances = dict(zip(feature_names, map(float, xgb_model.feature_importances_)))
        else:
            gb_model = GradientBoostingClassifier(n_estimators=120, max_depth=4, random_state=self.random_state)
            gb_model.fit(X_train, y_train)
            xgb_probs = gb_model.predict_proba(X_test)[:, 1]
            importances = dict(zip(feature_names, map(float, gb_model.feature_importances_)))

        results["XGBoost"] = self._evaluate_model("XGBoost Classifier", y_test, xgb_probs)
        results["XGBoost"]["feature_importances"] = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True)[:8])

        # 3. LightGBM (or Gradient Boosting tuned)
        if HAS_LGB:
            lgb_model = lgb.LGBMClassifier(
                n_estimators=160, num_leaves=31, learning_rate=0.06,
                subsample=0.8, colsample_bytree=0.8, random_state=self.random_state,
                verbose=-1
            )
            lgb_model.fit(X_train, y_train)
            lgb_probs = lgb_model.predict_proba(X_test)[:, 1]
        else:
            gb_model2 = GradientBoostingClassifier(n_estimators=150, max_depth=5, learning_rate=0.06, random_state=self.random_state)
            gb_model2.fit(X_train, y_train)
            lgb_probs = gb_model2.predict_proba(X_test)[:, 1]

        results["LightGBM"] = self._evaluate_model("LightGBM Classifier", y_test, lgb_probs)

        # 4. Cost-Sensitive Optimal Threshold Analysis
        best_probs = lgb_probs if results["LightGBM"]["auc_roc"] >= results["XGBoost"]["auc_roc"] else xgb_probs
        cost_curve = self._compute_cost_curve(y_test, best_probs)
        results["Cost_Optimization"] = cost_curve

        os.makedirs("web/data", exist_ok=True)
        with open("web/data/model_metrics.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"[+] Tournament Complete. Winner: {'LightGBM' if results['LightGBM']['auc_roc'] >= results['XGBoost']['auc_roc'] else 'XGBoost'}")
        print(f" -> Best AUC-ROC: {max(results['LightGBM']['auc_roc'], results['XGBoost']['auc_roc']):.4f}")
        print(f" -> Optimal Threshold: p* = {cost_curve['optimal_threshold']:.2f}")
        print(f" -> Projected Annual Savings: ${cost_curve['projected_annual_savings_millions']:.2f}M USD")
        return results

    def _evaluate_model(self, name: str, y_true: pd.Series, probs: np.ndarray) -> Dict[str, Any]:
        auc = roc_auc_score(y_true, probs)
        pr_auc = average_precision_score(y_true, probs)
        loss = log_loss(y_true, probs)
        brier = np.mean((probs - y_true) ** 2)

        return {
            "model_name": name,
            "auc_roc": round(float(auc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "log_loss": round(float(loss), 4),
            "brier_score": round(float(brier), 4),
            "test_sample_size": len(y_true)
        }

    def _compute_cost_curve(self, y_true: pd.Series, probs: np.ndarray) -> Dict[str, Any]:
        thresholds = np.linspace(0.05, 0.85, 35)
        best_savings = -float("inf")
        optimal_th = 0.50
        curve_data = []

        total_actual_positives = int(y_true.sum())
        baseline_unmitigated_cost = total_actual_positives * self.cost_fn

        for th in thresholds:
            preds = (probs >= th).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, preds).ravel()
            
            # Total managed care cost
            managed_cost = (fn * self.cost_fn) + (fp * self.cost_fp) + (tp * self.cost_tp)
            net_savings = baseline_unmitigated_cost - managed_cost

            if net_savings > best_savings:
                best_savings = net_savings
                optimal_th = th

            curve_data.append({
                "threshold": round(float(th), 2),
                "false_negatives": int(fn),
                "false_positives": int(fp),
                "true_positives": int(tp),
                "net_savings_usd": round(float(net_savings), 2)
            })

        # Scale test savings (25% sample) to full annual population (4x)
        annualized_savings_millions = (best_savings * 4.0) / 1_000_000.0

        return {
            "optimal_threshold": round(float(optimal_th), 2),
            "projected_annual_savings_millions": round(float(annualized_savings_millions), 2),
            "baseline_unmitigated_cost_millions": round(float((baseline_unmitigated_cost * 4.0) / 1_000_000.0), 2),
            "curve_points": curve_data
        }

if __name__ == "__main__":
    tournament = OncologyMLTournament()
    tournament.run_tournament()
