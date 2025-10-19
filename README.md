# MCA Insights Engine

Welcome to the slightly chaotic, very useful MCA Insights Engine — a little data playground that turns MCA snapshots, change logs and enriched datasets into searchable tables, bite-sized daily summaries and a chat interface that actually understands (some of) your questions about company data.

## What's in this folder

mca_insights_engine/
- data/
	- raw/          # raw downloads / original CSVs
	- processed/    # normalized/master CSVs used by the app (e.g. master_day3.csv)
	- change_logs/  # change_log_day2.csv, change_log_day3.csv, etc.
	- enriched/     # enriched_dataset.csv and other augmentation outputs
- scripts/
	- integrate_data.py   # data ingestion / merging helpers
	- detect_changes.py   # change detection logic (generates change logs)
	- enrich_data.py      # enrichment routines (Task C)
	- generate_summary.py # creates daily_summary_YYYY-MM-DD.json
	- app.py              # Streamlit UI (dashboard + chat)
- ai/
	- chatbot.py          # rule-based + optional LLM parsing + executor
- requirements.txt

## TL;DR — What you can do

- Browse and explore the processed MCA snapshots with a lovely Streamlit app.
- See change history visualisations and simple charts.
- Use the chat box to ask for things like “Show new incorporations in Maharashtra” or “List manufacturing companies with capital above 10 lakh”.
- Generate or view daily summary JSON files (in `data/`).

## Screenshots (placeholders)

Add your screenshots to the project and replace the paths below. The README expects four images:

- `docs/screenshots/streamlit_ui_1.png` — Streamlit main UI (Search tab)
- `docs/screenshots/streamlit_ui_2.png` — Streamlit chat or summary charts
- `docs/screenshots/summary_sample.png` — a PNG export of a summary table or chart
- `docs/screenshots/summary_sample.json.png` — a visual snapshot of the JSON summary (png render)

Example markdown image embeds (replace when ready):

![Streamlit UI - Search](docs/screenshots/streamlit_ui_1.png)
![Streamlit UI - Chat](docs/screenshots/streamlit_ui_2.png)
![Summary (PNG)](docs/screenshots/summary_sample.png)
![Summary JSON (PNG)](docs/screenshots/summary_sample.json.png)

If you prefer the raw JSON files, look in `data/` for `daily_summary_*.json`.

## Quick setup (Windows PowerShell)

Open PowerShell and run these commands (assumes Python and pip are installed). These commands create a venv, install requirements, and run the Streamlit app.

```powershell
# from the project root (where this README lives):
cd .
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
streamlit run .\scripts\app.py
```

If you don't want to run Streamlit and just want to use the chatbot as a CLI-ish helper:

```powershell
# from the project root (where this README lives):
cd .
.\.venv\Scripts\Activate.ps1
python -c "from scripts import chatbot; print(chatbot.answer_query('Show new incorporations in Maharashtra'))"
```

Notes:
- If you want LLM parsing for natural language, set `GEMINI_API_KEY` in a `.env` file in the project root (or system env). The `chatbot` will fall back to the rule-based parser if no key is found.
- Streamlit caches loaded CSVs to speed up repeat runs. Update or delete cache when experimenting heavily.

## Data expectations & helpful tips

- Place processed CSVs in `data/processed/` named like `master_day1.csv`, `master_day2.csv`, `master_day3.csv` — `app.py` and `chatbot.py` expect these filenames.
- Change logs: `data/change_logs/change_log_day2.csv` and `change_log_day3.csv`.
- Enriched dataset: `data/enriched/enriched_dataset.csv`.
- Daily summaries: `data/daily_summary_YYYY-MM-DD.json` (the app loads any `daily_summary_*.json` in `data/`).

Column name casing is handled lightly in the code, but if you see mysterious KeyError-like behaviour, double-check CSV headers and run the ingestion scripts in `scripts/`.

## Examples you can type into the chat

- "Show new incorporations in Maharashtra"
- "List all companies in the manufacturing sector with authorized capital above Rs.10 lakh"
- "How many companies were struck off last month?"

The rule-based parser handles many simple patterns; if GEMINI API key is set it will attempt an LLM parse first.

## FLOWCHART
flowchart TD

A[Raw MCA Datasets (5 CSVs)] --> B[Data Integration (integrate_data.py)]
B --> C[Processed Master Data (master_day1.csv)]
C --> D[Daily Change Simulation (detect_changes.py)]
D --> E[Change Logs (change_log_day2.csv, change_log_day3.csv)]
E --> F[Web Enrichment (enrich_data.py)]
F --> G[Enriched Dataset (enriched_dataset.csv)]
G --> H[AI Summaries (generate_summary.py)]
H --> I[Streamlit Dashboard (app.py)]
I --> J[Chatbot (chatbot.py)]
J --> K[GitHub Repository]
K --> L[Evaluation / Deployment]

subgraph "GitHub Repo Structure"
    B
    D
    F
    H
    I
    J
end


## Developer notes (if you poke around)

- `scripts/app.py` is the Streamlit front-end. It imports `chatbot` via `import chatbot as mca_chat` (relative import style), so ensure `scripts/` is on the Python path when running.
- `ai/chatbot.py` contains the parsing + executor (`answer_query(question)`). It reads `data/processed/master_day3.csv` as the main snapshot.
- `generate_summary.py` creates `daily_summary_YYYY-MM-DD.json` files that the app visualizes in the Daily Summaries tab.

## Want me to do more?


If you want any of those, say which one and I’ll sprout it like a good little dev plant.

## Setup & Environment

Make the project behave nicely by configuring a couple of environment values and (optionally) a `.env` file.

1) Create a `.env` in the project root (optional but convenient)

Example `.env` content (create a `.env` file in the project root next to this README):

```ini
# Place your Gemini API key here if you want the chatbot to use LLM parsing
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: set other env vars used by your scripts
# DATA_PATH=... (not required by default)
```

2) Load the `.env` automatically (the code already attempts to) or set an environment variable in PowerShell:

```powershell
# Load .env in the current session (requires the python-dotenv package) - not strictly necessary:
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('GEMINI_KEY', bool(os.getenv('GEMINI_API_KEY')) )"

# Or set the key directly in PowerShell for the current session:
$env:GEMINI_API_KEY='your_gemini_api_key_here'

# Confirm it's set:
python - << 'PY'
import os
print('Gemini key detected:', bool(os.getenv('GEMINI_API_KEY')))
PY
```

3) Notes on the GEMINI key and behaviour

- If `GEMINI_API_KEY` is present, `ai/chatbot.py` will attempt an LLM parse first and fall back to the rule-based parser on error.
- Keep your key secret. Do not commit `.env` to source control. Consider adding `.env` to `.gitignore`.

4) Troubleshooting

- If Streamlit won't start, confirm dependencies installed and that your virtualenv is active.
- If the chat returns generic tips ("Try: ..."), it means the parser couldn't map the question to an intent — try clearer phrasing or set the GEMINI key to improve parsing.


