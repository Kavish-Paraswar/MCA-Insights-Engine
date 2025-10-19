import pandas as pd, json
from pathlib import Path

B = Path(__file__).resolve().parents[1]
LOG = B/"data"/"change_logs"
OUT = B/"data"
OUT.mkdir(parents=True, exist_ok=True)

def summarize_log(p, date):
    df = pd.read_csv(p, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    new = (df["change_type"] == "New Incorporation").sum() if "change_type" in df.columns else 0
    dereg = (df["change_type"] == "Deregistered").sum() if "change_type" in df.columns else 0
    upd = (df["change_type"] == "Field Update").sum() if "change_type" in df.columns else 0
    return {"date": date, "new_incorporations": int(new),
            "deregistered": int(dereg), "updated_records": int(upd)}

if __name__ == "__main__":
    logs = {
        "2025-10-17": LOG/"change_log_day2.csv",
        "2025-10-18": LOG/"change_log_day3.csv"
    }
    summaries = []
    for date, path in logs.items():
        if path.exists():
            s = summarize_log(path, date)
            summaries.append(s)
            out = OUT/f"daily_summary_{date}.json"
            out.write_text(json.dumps(s, indent=2))
            print(f"[summary] wrote {out}")
    print("\n[done] summaries:", summaries)
