![WhatsApp Image 2025-10-19 at 14 38 14_c6d65b84](https://github.com/user-attachments/assets/3ba6f2e3-bf6b-43ff-ac05-a744df6cf372)![WhatsApp Image 2025-10-19 at 14 37 33_3982dea0](https://github.com/user-attachments/assets/e777ce50-4d91-436f-9c9a-6f3532902dec)# 🚀 MCA Insights Engine

Turning Ministry of Corporate Affairs (MCA) datasets into a clean, interactive insight engine — complete with daily change tracking, enrichment, summaries, and a conversational chatbot.

---

## 🧭 Overview

The **MCA Insights Engine** is a compact end-to-end data pipeline that:

- Cleans and integrates raw MCA datasets  
- Detects and logs daily company-level changes  
- Enriches data with web-based details  
- Generates daily AI-style summaries  
- Provides a Streamlit dashboard with search, filters, and a chat interface  

---

## ⚙️ Features

✅ Integrates & cleans raw MCA data  
✅ Detects incremental daily changes  
✅ Enriches data with public information  
✅ Generates daily summaries (`.json` / `.txt`)  
✅ Interactive Streamlit UI  
✅ Chatbot interface (rule-based + optional Gemini API)  

---

mca_insights_engine/
├── data/
│ ├── raw/ # Original MCA CSVs
│ ├── processed/ # Cleaned master data
│ ├── change_logs/ # Daily change logs
│ ├── enriched/ # Enriched datasets
│ └── daily_summary_*.json
├── scripts/
│ ├── integrate_data.py
│ ├── detect_changes.py
│ ├── enrich_data.py
│ ├── generate_summary.py
│ ├── chatbot.py
│ └── app.py
├── requirements.txt
├── .env.example
└── README.md



---

## ⚡ Quick Setup (Windows PowerShell)

# From the project root
cd .
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
streamlit run .\scripts\app.py
.\.venv\Scripts\Activate.ps1
python -c "from scripts import chatbot; print(chatbot.answer_query('Show new incorporations in Maharashtra'))"

---

📊 Data Requirements


| Folder              | Files                                                   | Purpose                   |
| ------------------- | ------------------------------------------------------- | ------------------------- |
| `data/processed/`   | `master_day1.csv`, `master_day2.csv`, `master_day3.csv` | Daily snapshots           |
| `data/change_logs/` | `change_log_day2.csv`, `change_log_day3.csv`            | Change detection output   |
| `data/enriched/`    | `enriched_dataset.csv`                                  | Web-enriched dataset      |
| `data/`             | `daily_summary_*.json`                                  | Generated daily summaries |

--- 

🖼️ Screenshots

| Section        | Image                                                     |
| -------------- | --------------------------------------------------------- |
| Search Tab     | ![Search UI](![WhatsApp Image 2025-10-19 at 14 37 33_3982dea0](https://github.com/user-attachments/assets/0aa6193f-162a-446d-8113-e14c6dc86e3f))|
| Chat Interface | ![Chat UI](![WhatsApp Image 2025-10-19 at 14 38 14_c6d65b84](https://github.com/user-attachments/assets/5677ba17-b352-4bc2-a398-d6758e0d8887))|
| Summary Chart  | ![Summary Chart](![WhatsApp Image 2025-10-19 at 14 38 27_a6f5bb95](https://github.com/user-attachments/assets/41857347-a625-4ad8-a591-84af4cff754b))|
| JSON Summary   | ![Summary JSON](![WhatsApp Image 2025-10-19 at 14 38 34_e785cbf2](https://github.com/user-attachments/assets/df2254b8-ca2d-4ada-b46c-6b354e6b8ee4))|

🔐 Environment Configuration

> Create a .env file in the project root:

GEMINI_API_KEY=your_gemini_api_key_here

 > Verify key detection

python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Gemini key found:', bool(os.getenv('GEMINI_API_KEY')))"
Keep .env private and add it to .gitignore.

---

🧠 Developer Notes

app.py → Streamlit UI (search, change history, summaries, chat)
chatbot.py → Conversational querying logic
generate_summary.py → Creates daily JSON summaries
The chatbot falls back to rule-based logic if no Gemini key is set.

📜 License

This project is open-sourced for educational and demonstration purposes.
You may reuse or adapt the code with attribution.

🧩 Tech Stack

Languages: Python
Frameworks: Streamlit, Pandas, Matplotlib
AI/LLM (Optional): Google Gemini API
Storage: CSV, JSON


