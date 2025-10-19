import pandas as pd
import numpy as np
from pathlib import Path

# ---------- paths ----------
BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"
CHANGE_LOGS = BASE / "data" / "change_logs"
CHANGE_LOGS.mkdir(parents=True, exist_ok=True)

# ---------- helpers ----------
def _num(s):
    if s is None: return np.nan
    s = pd.Series(s, dtype="object").astype(str).str.replace(",", "", regex=False)
    s = s.str.extract(r"(\d+(?:\.\d+)?)")[0]
    return pd.to_numeric(s, errors="coerce")

def _ensure_cols(df):
    # make sure the columns exist
    for c in ["authorized_capital","paid_up_capital","company_status","company_class",
              "principal_business_activity","nic_code","registered_office_address","roc","state"]:
        if c not in df.columns: df[c] = pd.NA
    return df

# ---------- simulate next day (vectorized) ----------
def simulate_next_day(prev_df: pd.DataFrame, day: str, seed=42):
    print(f"[simulate] start {day}  (rows={len(prev_df)})", flush=True)

    df = prev_df.copy()
    df = _ensure_cols(df)

    # normalize types we will touch
    ac = _num(df["authorized_capital"]).fillna(0.0).to_numpy()
    status = df["company_status"].astype("object").fillna("Active").to_numpy()

    n = len(df)
    if n == 0:
        df["snapshot_date"] = pd.Timestamp(day)
        return df

    rng = np.random.default_rng(seed)

    # choose indices once
    update_n = max(1, n // 100)          # ~1%
    remove_n = max(1, n // 200)          # ~0.5%
    idx_update = rng.choice(n, size=min(update_n, n), replace=False)
    idx_remove = rng.choice(n, size=min(remove_n, n), replace=False)

    # split updates half-half
    half = len(idx_update) // 2
    iu_cap = idx_update[:half]
    iu_stat = idx_update[half:]

    # authorized_capital: +5% or set to 100000 if zero
    ac[iu_cap] = np.where(ac[iu_cap] > 0, ac[iu_cap] * 1.05, 100000.0)

    # company_status: change to a different one
    statuses = np.array(["Active","Strike Off","Amalgamated","Under Process","Dormant"], dtype=object)
    # pick random status and ensure it's different from current
    rand_sta = rng.choice(statuses, size=len(iu_stat))
    same = rand_sta == status[iu_stat]
    if same.any():
        alt = rng.choice(statuses, size=int(same.sum()))
        rand_sta[same] = alt
    status[iu_stat] = rand_sta

    # apply back
    df.loc[:, "authorized_capital"] = ac
    df.loc[:, "company_status"] = status

    # remove rows
    keep_mask = np.ones(n, dtype=bool)
    keep_mask[idx_remove] = False
    df_removed = df.loc[keep_mask].reset_index(drop=True)

    # add new rows (same count as removed)
    add_n = int(remove_n)
    if add_n > 0:
        new_df = pd.DataFrame({
            "cin": [f"NEWCIN{day}{i:04d}" for i in range(add_n)],
            "company_name": [f"New Co {day} {i}" for i in range(add_n)],
            "company_class": ["Private"] * add_n,
            "date_of_incorporation": pd.Timestamp(day),
            "authorized_capital": [1_000_000.0] * add_n,
            "paid_up_capital": [100_000.0] * add_n,
            "company_status": ["Active"] * add_n,
            "principal_business_activity": ["Other business activities"] * add_n,
            "nic_code": ["7499"] * add_n,
            "registered_office_address": ["NA"] * add_n,
            "roc": ["ROC-NEW"] * add_n,
            "state": ["NA"] * add_n,
        })
        df_added = pd.concat([df_removed, new_df], ignore_index=True)
    else:
        df_added = df_removed

    df_added["snapshot_date"] = pd.Timestamp(day)
    print(f"[simulate] done {day}  (rows={len(df_added)}, +{add_n} new, -{remove_n} removed, ~{len(idx_update)} updates)", flush=True)
    return df_added

# ---------- change detection (vectorized) ----------
def detect_changes(prev: pd.DataFrame, curr: pd.DataFrame, date_label: str):
    print(f"[detect] {date_label}", flush=True)

    prev = prev.copy(); curr = curr.copy()
    for c in ["cin","company_status","company_class","state","company_name"]:
        if c in prev.columns: prev[c] = prev[c].astype(str)
        if c in curr.columns: curr[c] = curr[c].astype(str)

    prev["authorized_capital"] = _num(prev.get("authorized_capital", np.nan))
    curr["authorized_capital"] = _num(curr.get("authorized_capital", np.nan))
    prev["paid_up_capital"] = _num(prev.get("paid_up_capital", np.nan))
    curr["paid_up_capital"] = _num(curr.get("paid_up_capital", np.nan))

    prev_i = prev.set_index("cin")
    curr_i = curr.set_index("cin")

    # new / removed
    new_cin = curr_i.index.difference(prev_i.index)
    rem_cin = prev_i.index.difference(curr_i.index)

    # field diffs on intersection
    common = curr_i.index.intersection(prev_i.index)
    pc = prev_i.loc[common, ["company_status","authorized_capital","paid_up_capital","company_class"]]
    cc = curr_i.loc[common, ["company_status","authorized_capital","paid_up_capital","company_class"]]
    neq = pc != cc

    logs = []
    if not neq.empty:
        for col in ["company_status","authorized_capital","paid_up_capital","company_class"]:
            mask = neq[col].fillna(False)
            if mask.any():
                sub = pd.DataFrame({
                    "cin": pc.index[mask],
                    "change_type": "Field Update",
                    "field_changed": col,
                    "old_value": pc.loc[mask, col].to_numpy(),
                    "new_value": cc.loc[mask, col].to_numpy(),
                    "date": date_label
                })
                logs.append(sub)
    change_log = pd.concat(logs, ignore_index=True) if logs else pd.DataFrame(
        columns=["cin","change_type","field_changed","old_value","new_value","date"]
    )

    # add explicit records for new & deregistered (optional, but useful)
    if len(new_cin):
        change_log = pd.concat([
            change_log,
            pd.DataFrame({"cin": new_cin, "change_type": "New Incorporation",
                          "field_changed": pd.NA, "old_value": pd.NA, "new_value": pd.NA,
                          "date": date_label})
        ], ignore_index=True)
    if len(rem_cin):
        change_log = pd.concat([
            change_log,
            pd.DataFrame({"cin": rem_cin, "change_type": "Deregistered",
                          "field_changed": pd.NA, "old_value": pd.NA, "new_value": pd.NA,
                          "date": date_label})
        ], ignore_index=True)

    summary = pd.DataFrame([{
        "date": date_label,
        "new_incorporations": int(len(new_cin)),
        "deregistered": int(len(rem_cin)),
        "field_updates": int((change_log["change_type"] == "Field Update").sum())
    }])

    print(f"[detect] done {date_label}  (new={len(new_cin)}, dereg={len(rem_cin)}, field_updates={int((change_log['change_type']=='Field Update').sum())})", flush=True)
    return change_log, summary

# ---------- main ----------
if __name__ == "__main__":
    print("[load] reading Day 1 ...", flush=True)
    # read as object; convert numerics only for specific fields (faster + predictable)
    d1 = pd.read_csv(PROCESSED / "master_day1.csv", dtype="object", low_memory=False)
    print(f"[load] day1 rows={len(d1)}", flush=True)

    d2 = simulate_next_day(d1, "2025-10-17", seed=7)
    d3 = simulate_next_day(d2, "2025-10-18", seed=21)

    print("[save] writing Day2 / Day3 ...", flush=True)
    d2.to_csv(PROCESSED / "master_day2.csv", index=False)
    d3.to_csv(PROCESSED / "master_day3.csv", index=False)

    cl2, s2 = detect_changes(d1, d2, "2025-10-17")
    cl3, s3 = detect_changes(d2, d3, "2025-10-18")

    print("[save] writing change logs ...", flush=True)
    cl2.to_csv(CHANGE_LOGS / "change_log_day2.csv", index=False)
    cl3.to_csv(CHANGE_LOGS / "change_log_day3.csv", index=False)

    print("\n--- Daily Change Summary ---", flush=True)
    print(s2.to_string(index=False), flush=True)
    print(s3.to_string(index=False), flush=True)
    print("\n[done] logs:", CHANGE_LOGS, flush=True)
