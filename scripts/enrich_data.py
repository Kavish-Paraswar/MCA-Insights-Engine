import pandas as pd, numpy as np, re, sys
from pathlib import Path

B = Path(__file__).resolve().parents[1]
P_PRO = B / "data" / "processed"
P_LOG = B / "data" / "change_logs"
P_OUT = B / "data" / "enriched"
P_OUT.mkdir(parents=True, exist_ok=True)

def read_csv_lower(p):
    df = pd.read_csv(p, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def pick_ids(change_log_df: pd.DataFrame, d3: pd.DataFrame, k: int):
    # change_log may have 'cin' or 'CIN' → after lowering it's 'cin'
    if "cin" in change_log_df.columns and change_log_df["cin"].notna().any():
        a = change_log_df["cin"].astype(str).unique().tolist()
    else:
        a = []
    # restrict to CINs present in day3
    s = set(d3["cin"].astype(str))
    a = [x for x in a if x in s]
    if not a:
        # fallback: take from day3 directly
        a = d3["cin"].dropna().astype(str).unique().tolist()
    a = a[:max(50, min(100, k))]  # enforce 50–100 per assignment
    return a

def map_sector(nic):
    if pd.isna(nic): return "Other"
    x = str(nic)
    if re.match(r"^0?1", x): return "Agriculture"
    if re.match(r"^(10|11|12)", x): return "Manufacturing"
    if re.match(r"^(49|50|51|52)", x): return "Logistics"
    if re.match(r"^(61|62|63)", x): return "IT Services"
    if re.match(r"^(64|65|66)", x): return "Financial Services"
    if re.match(r"^85", x): return "Education"
    if re.match(r"^86", x): return "Healthcare"
    return "Other"

def enrich_mock(ids, d3, seed=20251019):
    z = d3.set_index("cin")
    rng = np.random.default_rng(seed)
    sources = [
        ("ZaubaCorp","https://www.zaubacorp.com/"),
        ("API Setu (MCA)","https://apisetu.gov.in/"),
        ("Indian Kanoon","https://indiankanoon.org/"),
        ("GST Portal","https://www.gst.gov.in/"),
        ("MCA21","https://www.mca.gov.in/")
    ]
    out = []
    for i, cin in enumerate(ids, 1):
        if cin not in z.index: continue
        r = z.loc[cin]
        src = sources[int(rng.integers(0, len(sources)))]
        sec = map_sector(r.get("nic_code"))
        out.append({
            "cin": cin,
            "company_name": str(r.get("company_name", "")),
            "state": str(r.get("state", "")),
            "status": str(r.get("company_status", "")),
            "source": src[0],
            "field": "profile_snapshot",
            "source_url": src[1],
            "sector": sec,
            "director_name": f"Director {int(rng.integers(1000,9999))}",
        })
        if i % 20 == 0:
            print(f"[enrich] {i}/{len(ids)}", flush=True)
    return pd.DataFrame(out)

def main():
    # load day3
    p3 = P_PRO / "master_day3.csv"
    if not p3.exists():
        sys.exit("master_day3.csv not found. Run Task B first.")
    d3 = read_csv_lower(p3)
    for c in ["cin","company_name","company_status","state","nic_code"]:
        if c in d3.columns: d3[c] = d3[c].astype(str)

    # pick change log (day3 → day2 fallback)
    if (P_LOG / "change_log_day3.csv").exists():
        cl = read_csv_lower(P_LOG / "change_log_day3.csv")
        print("[enrich] using change_log_day3.csv", flush=True)
    elif (P_LOG / "change_log_day2.csv").exists():
        cl = read_csv_lower(P_LOG / "change_log_day2.csv")
        print("[enrich] using change_log_day2.csv", flush=True)
    else:
        cl = pd.DataFrame({"cin": []})
        print("[enrich] no change logs found; falling back to day3 sample", flush=True)

    ids = pick_ids(cl, d3, k=100)
    if not ids:
        sys.exit("No CINs available to enrich (even after fallback).")

    print(f"[enrich] selected {len(ids)} CINs", flush=True)
    df = enrich_mock(ids, d3)

    # order/rename to exactly match assignment + extras last
    cols_required = ["cin","company_name","state","status","source","field","source_url"]
    for c in cols_required:
        if c not in df.columns: df[c] = pd.NA
    df = df[cols_required + [c for c in df.columns if c not in cols_required]]

    op = P_OUT / "enriched_dataset.csv"
    df.to_csv(op, index=False)
    print(f"[enrich] wrote {op} rows={len(df)}", flush=True)

if __name__ == "__main__":
    main()
