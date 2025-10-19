import os, re, json
import pandas as pd
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

B = Path(__file__).resolve().parents[1]
P_PRO = B / "data" / "processed"
P_LOG = B / "data" / "change_logs"
P_ENR = B / "data" / "enriched"


# ---------------- LOAD DATA ----------------
def load_data():
    d3 = pd.read_csv(P_PRO / "master_day3.csv", low_memory=False)
    for c in ["cin","company_name","company_status","state","company_class","principal_business_activity","nic_code"]:
        if c in d3.columns:
            d3[c] = d3[c].astype(str)

    for cap in ["authorized_capital","paid_up_capital"]:
        if cap in d3.columns:
            d3[cap] = pd.to_numeric(d3[cap], errors="coerce")

    cls = []
    for p in [P_LOG / "change_log_day2.csv", P_LOG / "change_log_day3.csv"]:
        if p.exists():
            x = pd.read_csv(p, low_memory=False)
            x.columns = [c.strip().lower() for c in x.columns]
            cls.append(x)
    ch = pd.concat(cls, ignore_index=True) if cls else pd.DataFrame(columns=["cin","change_type","field_changed","old_value","new_value","date"])

    enr = pd.DataFrame()
    pe = P_ENR / "enriched_dataset.csv"
    if pe.exists():
        enr = pd.read_csv(pe, low_memory=False)
        enr.columns = [c.strip().lower() for c in enr.columns]

    return d3, ch, enr


# ---------------- RULE-BASED PARSER ----------------
def parse_query(q: str):
    s = q.lower()
    filters = {}

    if "new" in s and "incorpor" in s:
        m = re.search(r"in\s+([a-z ]+)", s)
        if m:
            filters["state"] = m.group(1).strip().title()
        return "new_incorporations", filters

    if "manufacturing" in s or "sector" in s:
        filters["sector"] = "Manufacturing"
        m = re.search(r"above\s+rs\.?\s*([\d,]+)\s*(lakh|crore)?", s)
        if m:
            val = float(m.group(1).replace(",", ""))
            if m.group(2) and "lakh" in m.group(2).lower():
                val *= 1e5
            elif m.group(2) and "crore" in m.group(2).lower():
                val *= 1e7
            filters["min_capital"] = val
        return "sector_capital", filters

    if "struck off" in s or "deregister" in s:
        if "last month" in s or "last 30" in s:
            return "struck_last_month", {}
        return "struck_total", {}

    return "unknown", {}


# ---------------- EXECUTION LOGIC ----------------
def execute(intent, filters, d3, ch, enr):
    if intent == "new_incorporations":
        df = d3[d3["cin"].astype(str).str.startswith("NEWCIN", na=False) |
                d3["company_name"].str.contains("New Co", case=False, na=False)]
        if "state" in filters:
            df = df[df["state"].str.contains(filters["state"], case=False, na=False)]
        msg = f"{len(df)} new incorporations"
        if "state" in filters:
            msg += f" in {filters['state']}"
        msg += "."
        return msg, df.head(50)

    if intent == "sector_capital":
        if enr.empty:
            return "No enriched dataset found.", pd.DataFrame()
        df = enr.copy()
        if "sector" in filters:
            df = df[df["sector"].str.contains(filters["sector"], case=False, na=False)]
        if "min_capital" in filters and "authorized_capital" in df.columns:
            df["authorized_capital"] = pd.to_numeric(df["authorized_capital"], errors="coerce")
            df = df[df["authorized_capital"].fillna(0) >= filters["min_capital"]]
        msg = f"Found {len(df)} companies in {filters.get('sector','the sector')}"
        if "min_capital" in filters:
            msg += f" with authorized capital above Rs.{int(filters['min_capital']):,}"
        msg += "."
        return msg, df.head(50)

    if intent == "struck_last_month":
        if ch.empty:
            return "No change logs available.", pd.DataFrame()
        ch["date"] = pd.to_datetime(ch.get("date"), errors="coerce")
        recent = ch[ch["change_type"].str.contains("Deregistered", case=False, na=False)]
        msg = f"{recent['cin'].nunique()} companies were struck off last month."
        return msg, recent.head(50)

    if intent == "struck_total":
        cnt = (d3["company_status"].str.contains("Strike Off", case=False, na=False)).sum()
        msg = f"{cnt} companies are currently marked as 'Strike Off'."
        return msg, pd.DataFrame()

    return "I couldn’t understand your question. Try one of the examples below.", pd.DataFrame()


# ---------------- MAIN ENTRY ----------------
def answer_query(q: str):
    d3, ch, enr = load_data()
    intent, filters = parse_query(q)
    msg, df = execute(intent, filters, d3, ch, enr)
    return msg, df
