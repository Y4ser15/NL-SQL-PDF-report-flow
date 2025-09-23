# NL → SQL → JSON → LLM → PDF (Langflow)

A Langflow flow that turns natural-language questions into SQLite SQL, summarizes results with an LLM, and generates a PDF via a custom component. Includes a tiny HTML chatbot page for quick testing.

## Quick start
1) Create & activate venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

2) Install minimal deps
pip install -r requirements.txt

3) (Optional) Create the SQLite DB with mock data
python setup_database.py    # writes sample_data.db in this folder

4) Run Langflow
langflow run  # open the URL shown in terminal, set your LLM key in the UI if needed


## Import & run the flow

In Langflow UI → Import → select flows/nl_to_sql_json_to_pdf_report.json.

Ensure sample_data.db is in this folder (or set SQLITE_DB_PATH in .env; see below).

*Ensure to add the right path in the SQL Database node, and the openai key in the LLM nodes.*

Click Play on the flow and try:

Customer count by state

Total revenue in the last 30 days

The final node returns a path to the generated PDF (default ./reports/report.pdf).

## Simple HTML tester (optional)

Open web/chatbot.html directly, or serve the folder:

python -m http.server 8000
then open http://localhost:8000/web/chatbot.html


Use it to send quick prompts and verify answers before exporting to PDF.