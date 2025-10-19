import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import chatbot as mca_chat


# ---------- paths ----------
BASE = Path(__file__).resolve().parents[1]
P_PRO = BASE / "data" / "processed"
P_LOG = BASE / "data" / "change_logs"
P_ENR = BASE / "data" / "enriched"
P_SUM = BASE / "data"

st.set_page_config(page_title="MCA Insights Engine", layout="wide")
st.title("MCA Insights Engine")

# ---------- load helpers ----------
def _read_csv(path):
    if not path.exists(): return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    return df

@st.cache_data
def load_all():
    d1 = _read_csv(P_PRO/"master_day1.csv")
    d2 = _read_csv(P_PRO/"master_day2.csv")
    d3 = _read_csv(P_PRO/"master_day3.csv")

    # normalize date/year safely
    for df in (d1, d2, d3):
        if "date_of_incorporation" in df.columns:
            df["date_of_incorporation"] = pd.to_datetime(df["date_of_incorporation"], errors="coerce")
            yr = pd.to_numeric(df["date_of_incorporation"].dt.year, errors="coerce")
            df["year"] = yr.astype("Int64")

        # ensure string columns are strings
        for c in ["cin", "company_name", "state", "company_status"]:
            if c in df.columns:
                df[c] = df[c].astype(str)

    cl2 = _read_csv(P_LOG/"change_log_day2.csv")
    cl3 = _read_csv(P_LOG/"change_log_day3.csv")
    for cl in (cl2, cl3):
        if not cl.empty:
            cl.columns = [c.strip().lower() for c in cl.columns]
            if "date" not in cl.columns:
                cl["date"] = pd.NaT

    enr = _read_csv(P_ENR/"enriched_dataset.csv")
    if not enr.empty:
        enr.columns = [c.strip().lower() for c in enr.columns]

    return d1, d2, d3, cl2, cl3, enr

d1, d2, d3, cl2, cl3, enr = load_all()

def uniq(values):
    s = pd.Series(values).dropna().astype(str)
    s = s[s.ne("") & s.ne("nan")]
    out = sorted(s.unique().tolist())
    return out

# ---------- UI ----------
tab1, tab2, tab3, tab4 = st.tabs(["Search", "Change History", "Enriched", "Daily Summaries"])

# --- Search tab ---
with tab1:
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        q = st.text_input("Search by CIN or Company Name")
    with col2:
        # build a clean, int year list without '2025.0' issue
        years = []
        if "year" in d3.columns:
            years = pd.to_numeric(d3["year"], errors="coerce").dropna().astype(int).unique().tolist()
            years = sorted(years)
        year_sel = st.selectbox("Year", ["All"] + years) if years else "All"
    with col3:
        state_sel = st.selectbox("State", ["All"] + uniq(d3.get("state", []))) if not d3.empty else "All"
    with col4:
        status_sel = st.selectbox("Status", ["All"] + uniq(d3.get("company_status", []))) if not d3.empty else "All"

    z = d3.copy()
    if q:
        t = q.strip().upper()
        z = z[
            z["cin"].astype(str).str.upper().str.contains(t) |
            z["company_name"].astype(str).str.upper().str.contains(t, na=False)
        ]
    if year_sel != "All" and "year" in z.columns:
        z = z[pd.to_numeric(z["year"], errors="coerce").astype("Int64") == int(year_sel)]
    if state_sel != "All":
        z = z[z["state"] == state_sel]
    if status_sel != "All":
        z = z[z["company_status"] == status_sel]

    st.write(f"Rows: {len(z)}")
    st.dataframe(z.head(300), use_container_width=True)

    # show change history for a single CIN query (if provided)
    if q and (not cl2.empty or not cl3.empty):
        t = q.strip().upper()
        ch = pd.concat([cl2, cl3], ignore_index=True)
        ch = ch[ch["cin"].astype(str).str.upper() == t] if "cin" in ch.columns else pd.DataFrame()
        if not ch.empty:
            st.subheader("Change history for selection")
            st.dataframe(ch, use_container_width=True)

# --- Change History tab ---
with tab2:
    if cl2.empty and cl3.empty:
        st.info("No change logs found.")
    else:
        ch = pd.concat([cl2.assign(day="Day2"), cl3.assign(day="Day3")], ignore_index=True)
        if "change_type" in ch.columns:
            g = ch.groupby(["day", "change_type"]).size().rename("count").reset_index()
            pivot = g.pivot(index="day", columns="change_type", values="count").fillna(0).astype(int)
            st.dataframe(pivot, use_container_width=True)

            fig = plt.figure()
            pivot.plot(kind="bar", ax=plt.gca())
            plt.ylabel("Count")
            plt.title("Change counts by day")
            st.pyplot(fig, clear_figure=True)
        else:
            st.dataframe(ch, use_container_width=True)

# --- Enriched tab ---
with tab3:
    if enr.empty:
        st.info("No enriched dataset found. Run Task C.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            src = st.selectbox("Source", ["All"] + uniq(enr.get("source", [])))
        with c2:
            sec = st.selectbox("Sector", ["All"] + uniq(enr.get("sector", []))) if "sector" in enr.columns else "All"
        ez = enr.copy()
        if src != "All": ez = ez[ez["source"] == src]
        if sec != "All" and "sector" in ez.columns: ez = ez[ez["sector"] == sec]
        st.write(f"Rows: {len(ez)}")
        st.dataframe(ez.head(300), use_container_width=True)

# --- Daily Summaries tab ---
with tab4:
    import json
    rows = []
    for p in sorted(P_SUM.glob("daily_summary_*.json")):
        try:
            rows.append(json.loads(p.read_text()))
        except Exception:
            pass
    if rows:
        s = pd.DataFrame(rows)
        st.dataframe(s, use_container_width=True)
        if set(["new_incorporations","deregistered","updated_records"]).issubset(s.columns):
            fig2 = plt.figure()
            s.set_index("date")[["new_incorporations","deregistered","updated_records"]].plot(kind="bar", ax=plt.gca())
            plt.title("Daily Summary")
            st.pyplot(fig2, clear_figure=True)
    else:
        st.info("No daily summaries found.")

# --- CHAT TAB ---
tab_chat = st.tabs(["Chat with MCA Data"])[0]
with tab_chat:
    st.subheader("Chat with MCA Data")
    st.caption("Examples:")
    st.code("Show new incorporations in Maharashtra.", language="text")
    st.code("List all companies in the manufacturing sector with authorized capital above Rs.10 lakh.", language="text")
    st.code("How many companies were struck off last month?", language="text")

    q = st.chat_input("Ask your question...")
    if q:
        with st.spinner("Processing..."):
            msg, table = mca_chat.answer_query(q)
        st.write(msg)
        if isinstance(table, pd.DataFrame) and not table.empty:
            st.dataframe(table, use_container_width=True)
