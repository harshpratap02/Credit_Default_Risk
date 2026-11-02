import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline

sys.path.append(os.path.dirname(__file__))

from data import TARGET, load_clean
from features import add_features, build_preprocess

SEED = 42
POLICY_RATIO = 5
RATIOS = [1, 2, 3, 5, 7, 10, 15, 20]
CUTOFFS = np.round(np.arange(0.02, 0.90, 0.01), 2)
MONOTONIC_CONSTRAINTS = {
    "MAX_DELAY": 1,
    "LATE_MONTHS": 1,
    "UTIL_AVG": 1,
    "PAYRATIO_AVG": -1,
    "PAYRATIO_TOTAL": -1,
}


def build_model(X):
    preprocessor = (
        build_preprocess(X, scale=False)
        .set_params(verbose_feature_names_out=False)
        .set_output(transform="pandas")
    )
    return Pipeline([
        ("prep", preprocessor),
        ("clf", HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=400,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            early_stopping=True,
            validation_fraction=0.1,
            monotonic_cst=MONOTONIC_CONSTRAINTS,
            random_state=SEED,
        )),
    ])


def policy_cost(prob, actual, cutoff, ratio):
    approved = prob < cutoff
    missed_defaults = np.sum(approved & (actual == 1))
    rejected_good = np.sum(~approved & (actual == 0))
    return ratio * missed_defaults + rejected_good


def select_cutoff(prob, actual, ratio):
    costs = [policy_cost(prob, actual, c, ratio) for c in CUTOFFS]
    return float(CUTOFFS[int(np.argmin(costs))])


def evaluate_policy(prob, actual, cutoff, ratio):
    approved = prob < cutoff
    cost = policy_cost(prob, actual, cutoff, ratio)
    approve_all = ratio * actual.sum()
    reject_all = (actual == 0).sum()
    return {
        "cost_ratio": ratio,
        "theoretical_cutoff": round(1 / (1 + ratio), 3),
        "chosen_cutoff": cutoff,
        "approval_rate": float(approved.mean()),
        "bad_rate_among_approved": float(actual[approved].mean()),
        "defaults_rejected": float(1 - actual[approved].sum() / actual.sum()),
        "saving_vs_approve_all": float(1 - cost / approve_all),
        "saving_vs_best_naive": float(1 - cost / min(approve_all, reject_all)),
    }


def main():
    os.makedirs("reports", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    full = add_features(load_clean())
    X, y = full.drop(columns=TARGET), full[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    oof_prob = cross_val_predict(
        build_model(X), X_train, y_train, cv=cv, method="predict_proba", n_jobs=-1
    )[:, 1]

    model = build_model(X).fit(X_train, y_train)
    test_prob = model.predict_proba(X_test)[:, 1]
    train_actual, test_actual = y_train.values, y_test.values

    rows = [
        evaluate_policy(test_prob, test_actual, select_cutoff(oof_prob, train_actual, r), r)
        for r in RATIOS
    ]
    sensitivity = pd.DataFrame(rows)
    sensitivity.to_csv("reports/pipeline_cost_sensitivity.csv", index=False)
    policy = sensitivity.loc[sensitivity["cost_ratio"] == POLICY_RATIO].iloc[0]

    fpr, tpr, _ = roc_curve(test_actual, test_prob)
    metrics = {
        "model": "HistGradientBoosting (monotonic)",
        "roc_auc": float(roc_auc_score(test_actual, test_prob)),
        "pr_auc": float(average_precision_score(test_actual, test_prob)),
        "ks": float((tpr - fpr).max()),
        "policy_cost_ratio": POLICY_RATIO,
        "cutoff": float(policy["chosen_cutoff"]),
        "approval_rate": float(policy["approval_rate"]),
        "bad_rate_among_approved": float(policy["bad_rate_among_approved"]),
        "saving_vs_approve_all": float(policy["saving_vs_approve_all"]),
        "saving_vs_best_naive": float(policy["saving_vs_best_naive"]),
    }

    with open("reports/metrics.json", "w") as handle:
        json.dump(metrics, handle, indent=2)
    joblib.dump(model, "models/hgb_monotonic.joblib")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
