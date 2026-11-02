import glob
import io
import os
import urllib.request
import zipfile

import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
CLEAN_PATH = "data/credit_clean.csv"
SEARCH_DIRS = ["/content", "data"]
EXTENSIONS = (".xls", ".xlsx", ".csv")
TARGET = "DEFAULT_FLAG"
EXPECTED_ROWS = 30000
REQUIRED_COLUMNS = {"LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE", TARGET}

TARGET_ALIASES = {
    "default payment next month": TARGET,
    "default.payment.next.month": TARGET,
    "PAY_0": "PAY_1",
}


def find_local_file():
    for directory in SEARCH_DIRS:
        for path in sorted(glob.glob(os.path.join(directory, "*"))):
            name = os.path.basename(path).lower()
            if name == os.path.basename(CLEAN_PATH):
                continue
            if name.endswith(EXTENSIONS) and ("default" in name or "credit" in name):
                return path
    return None


def read_raw(path):
    if path.lower().endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path, header=1)


def download_raw():
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    payload = urllib.request.urlopen(request).read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        member = [n for n in archive.namelist() if n.lower().endswith((".xls", ".xlsx"))][0]
        return pd.read_excel(io.BytesIO(archive.read(member)), header=1)


def standardize(df):
    df = df.rename(columns=TARGET_ALIASES)
    df["EDUCATION"] = df["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    df["MARRIAGE"] = df["MARRIAGE"].replace({0: 3})
    return df


def validate(df):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, found {len(df)}")
    return df


def load_clean():
    if os.path.exists(CLEAN_PATH):
        return pd.read_csv(CLEAN_PATH)

    local_path = find_local_file()
    raw = read_raw(local_path) if local_path else download_raw()
    df = validate(standardize(raw))
    df.to_csv(CLEAN_PATH, index=False)
    return df
