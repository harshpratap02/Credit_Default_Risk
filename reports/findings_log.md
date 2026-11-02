 Findings log (final figures)

SQL and statistical tests
- Default rate rises from 11.7% with no late months to 70.3% with six. Customers 2+ months late on the latest bill default at about 69%, against 34% at one month late.
- Latest payment status has the strongest association with default (Cramer's V 0.42). Sex, marriage and education are significant but negligible (V of 0.07 or less).
- Credit limit is inversely related to default (36% under 50k, 12% above 400k). Age is U-shaped (27% under 25, 20% at 25 to 34, 27% at 55+) and a rank test misses it (p = 0.37).
- Caveats: the Education "Other" group (n = 468) merges undocumented codes. PAY_1 values 5 to 8 have fewer than 30 customers each. Some chi-square cells have expected counts under 5.

Features
- 43 columns after engineering. LATE_MONTHS (r = +0.40) and MAX_DELAY (r = +0.33) are the strongest. BILL_TREND is near zero (r = -0.02).

Models (test set of 6,000)
- 5-fold CV ROC-AUC: logistic regression 0.762, boosting 0.787, monotonic boosting 0.787.
- Test ROC-AUC / PR-AUC / KS: logistic 0.746 / 0.505 / 0.391, boosting 0.781 / 0.556 / 0.428, monotonic 0.780 / 0.557 / 0.429. Random PR-AUC is 0.221.
- Calibration is good: mean predicted 0.221, observed 0.221. Class weights were not used.
- At a 0.50 cutoff boosting catches only 483 of 1,327 defaulters, so 0.50 is unsuitable for lending.
- Decile lift: top decile defaults at 69.8% (3.16x), the riskiest 20% contain 50.6% of defaults.
- Permutation importance is led by MAX_DELAY and PAY_1. Demographics contribute almost nothing.

Business layer (5:1 cost ratio, monotonic model, cutoff chosen on out-of-fold predictions)
- Cutoff 0.16 (theoretical 0.167), approval 53.4% [52.1, 54.6], bad rate among approved 9.7% [8.6, 10.6] against 22.1%.
- Saving 28.8% [24.8, 32.9] against the best naive policy (reject all), 49.9% against approve all.
- The naive baseline flips at a ratio of about 3.5. Chosen cutoffs stay within 0.025 of theory from 1x to 20x. Ratios of 15x and 20x are not practical operating points.
- Cutoffs from 0.15 to 0.20 are within about 3% of optimal cost.

Monotonic constraint
- Paired ROC-AUC difference vs unconstrained: -0.0008 [-0.0027, 0.0011]. No detectable cost.
- Feature sweep: 6 small violations in the unconstrained model, none in the constrained one.

Fairness audit (5x policy, cutoff 0.16)
- Disparate impact: male 0.859, university 0.807, high school 0.747, under 25 0.695. Under 25 is below 0.80 in 99.8% of bootstrap replicates, high school 96.9%, university 38.1%, male 0.4%.
- Approved high school customers default 4.8 points more than approved graduate school customers [1.4, 8.1].
- Dropping SEX, MARRIAGE and AGE: ROC-AUC -0.0006 [-0.0025, 0.0014], male false positive gap down 0.042, under 25 disparate impact down 0.053 [0.016, 0.090].
- Approval-rate disparate impact depends on volume: under 25 is 0.823 at 70.6% approval and about 0.68 at 52.9%.
- Bootstrap intervals cover test-sample noise only (not retraining or cutoff selection). About 20 comparisons were made.

Exposure-aware expected-profit policy (simulated economics)
- Base case (CCF 0.5, ratio 5): profit per applicant 0.910 flat tuned (cutoff 0.23), 1.140 exposure-aware (+229.7 per 1,000 [187.9, 274.2]). Positive in all 16 scenarios tested.
- Uplift survives margin-floor changes (206.6 at the 25th percentile, 93.7 at the 50th) and matched approval volume (+281.6 per 1,000 [226.4, 335.0]). It does not come from a lower bad rate (12.4% vs 9.6% matched).
- Near-zero cutoffs (16.4% of customers) are high-limit, near-dormant accounts.
- Disparate impact flips above 1 (under 25: 0.682 to 1.134 at equal volume), a reversal driven by the credit-limit proxy, not evidence of fairness.
- Profit is simulated from assumed economics, so it shows the method, not money gained.
