# scripts/10_integrate_data.py
import pandas as pd, numpy as np, pathlib, re
from tqdm import tqdm

RAW = pathlib.Path("data/raw")
OUT = pathlib.Path("data/processed"); OUT.mkdir(parents=True, exist_ok=True)

# map many-to-one headers → canonical
CANON = {
    "cin": ["cin","corporate_identification_number"],
    "company_name": ["company_name","name_of_company","companyname"],
    "company_class": ["class_of_company","company_class","class"],
    "date_of_incorporation": ["date_of_incorporation","incorporation_date","dateofincorporation"],
    "authorized_capital": ["authorized_capital","authorised_capital","authorized_capital_(rs)"],
    "paid_up_capital": ["paid_up_capital","paidup_capital","paid_up_capital_(rs)"],
    "company_status": ["company_status","status","company_status_(for_efiling)"],
    "principal_business_activity": ["principal_business_activity","principal_business_activity_as_per_cin","nic_code_description"],
    "nic_code": ["nic_code","principal_business_activity_as_per_cin_code","nic"],
    "registered_office_address": ["registered_office_address","reg_office_address","address"],
    "roc": ["roc","roc_code","roc_name"],
    "state": ["state","state_name","registered_state"],
}

def pick(df, names):
    for n in names:
        if n in df.columns: return df[n]
    return pd.Series([pd.NA]*len(df))

def coerce_cap(s):
    s = s.astype(str).str.replace(",","",regex=False)
    s = s.str.extract(r"(\d+(?:\.\d+)?)")[0]
    return pd.to_numeric(s, errors="coerce")

def normalize_chunk(df):
    df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
    out = pd.DataFrame()
    for k, alts in CANON.items():
        out[k] = pick(df, alts)
    out["cin"] = out["cin"].astype(str).str.strip().str.upper()
    out["date_of_incorporation"] = pd.to_datetime(out["date_of_incorporation"], errors="coerce")
    out["authorized_capital"] = coerce_cap(out["authorized_capital"])
    out["paid_up_capital"] = coerce_cap(out["paid_up_capital"])
    # crude state fallback from ROC text
    m = out["state"].isna() & out["roc"].notna()
    out.loc[m, "state"] = out.loc[m, "roc"].astype(str).str.extract(r"ROC[-\s]?([\w\s]+)", expand=False)
    return out

def read_all_canonical():
    frames = []
    for p in RAW.glob("*.csv"):
        for chunk in pd.read_csv(p, chunksize=200_000, low_memory=False, encoding_errors="ignore"):
            frames.append(normalize_chunk(chunk))
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["cin"]).drop_duplicates(subset=["cin"])
    return df

if __name__ == "__main__":
    df = read_all_canonical()
    df["snapshot_date"] = pd.Timestamp("2025-10-16")  # Day 1
    df.to_csv(OUT/"master_day1.csv", index=False)
    print("Wrote", OUT/"master_day1.csv", "rows:", len(df))
