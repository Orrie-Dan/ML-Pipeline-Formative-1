# Task 3 — Database Design & Implementation (SQL + MongoDB)

Celyn's contribution. Stores the real PJME hourly energy dataset in **MySQL**
(relational star schema) and **MongoDB** (denormalized documents), and runs the
required time-series queries against both.

## Contents

| File | What it is |
|------|-----------|
| `schema.sql` | MySQL star schema — `regions`, `datetime_dim`, `energy_readings` (3 tables) |
| `erd_diagram.png` / `erd_diagram.md` | ERD image + Mermaid source |
| `sql_loader.py` | Loads `clean_energy_dataset.csv` into MySQL |
| `mongo_loader.py` | Loads the same CSV into MongoDB |
| `sql_queries.py` | Runs 4 queries on MySQL, writes results to `query_results.md` |
| `mongo_queries.py` | Runs 4 queries on MongoDB, writes results to `query_results.md` |
| `sample_mongo_documents.json` | Example MongoDB documents |
| `query_results.md` | Captured output of all queries (the graded evidence) |
| `Task3_Database_Design.md` | Report section (schema rationale, SQL-vs-Mongo, queries) |
| `db_config.py` | Shared `.env` loader + connection config |
| `.env.example` | Credential template (copy to `.env`) |

## Setup

```bash
cd task3_database
python -m venv venv && source venv/bin/activate     # optional
pip install -r requirements.txt
cp .env.example .env      # then edit .env with your Railway + Atlas credentials
```

- **MySQL**: create a free database on [Railway](https://railway.app) → "Provision MySQL".
- **MongoDB**: create a free **M0** cluster on [MongoDB Atlas](https://www.mongodb.com/atlas).

Put both sets of credentials in `.env`. The dataset (`clean_energy_dataset.csv`)
lives in the repo root and is read automatically.

## Run

```bash
# 1. Load data (use --limit for a quick demo; drop it to load all 145k rows)
python sql_loader.py   --reset --limit 10000
python mongo_loader.py --reset --limit 10000

# 2. Run the queries — this fills query_results.md with real output
python sql_queries.py
python mongo_queries.py

# 3. (Optional) regenerate the ERD image
python erd_render.py
```

After step 2, open `query_results.md` — it now contains the actual query output
to submit and to paste into the report.

## Notes

- This folder is **self-contained** and does not modify the rest of the repo.
- `.env` must never be committed (it is git-ignored).
- The schema here (`regions` / `datetime_dim` / `energy_readings`) is a normalized
  star schema chosen for time-series slicing; see `Task3_Database_Design.md` for
  the rationale and the SQL-vs-MongoDB comparison.
