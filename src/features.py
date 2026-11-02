import numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PAY  = [f"PAY_{i}" for i in range(1, 7)]
BILL = [f"BILL_AMT{i}" for i in range(1, 7)]
AMT  = [f"PAY_AMT{i}" for i in range(1, 7)]
CAT  = ["SEX", "EDUCATION", "MARRIAGE"]

def add_features(df):
    d = df.copy()
    for i in range(1, 7):
        d[f"UTIL_{i}"] = d[f"BILL_AMT{i}"] / d["LIMIT_BAL"]                 # credit utilization
    util = [f"UTIL_{i}" for i in range(1, 7)]
    d["UTIL_AVG"], d["UTIL_MAX"] = d[util].mean(axis=1), d[util].max(axis=1)

    bill_pos = d[BILL].clip(lower=0)
    for i in range(1, 7):                                                  # payment-to-bill ratio
        r = d[f"PAY_AMT{i}"] / bill_pos[f"BILL_AMT{i}"].replace(0, np.nan)
        d[f"PAYRATIO_{i}"] = r.clip(0, 1).fillna(1.0)                      # no bill -> nothing owed
    d["PAYRATIO_AVG"] = d[[f"PAYRATIO_{i}" for i in range(1, 7)]].mean(axis=1)
    tot = (d[AMT].sum(axis=1) / bill_pos.sum(axis=1).replace(0, np.nan)).clip(0, 1)
    d["PAYRATIO_TOTAL"] = tot.fillna(1.0)

    d["MAX_DELAY"]   = d[PAY].max(axis=1)                                   # worst delay
    d["LATE_MONTHS"] = (d[PAY] > 0).sum(axis=1)                             # months late
    d["REVOLVING_MONTHS"] = (d[PAY] == 0).sum(axis=1)
    d["BILL_TREND"]  = (d["BILL_AMT1"] - d["BILL_AMT6"]) / d["LIMIT_BAL"]   # debt growth vs limit
    return d.drop(columns=["ID"], errors="ignore")

def build_preprocess(X, scale):
    num = [c for c in X.columns if c not in CAT]
    return ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
         ("num", StandardScaler() if scale else "passthrough", num)],
        sparse_threshold=0)
