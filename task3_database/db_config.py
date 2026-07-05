"""Shared configuration + tiny .env loader for the Task 3 database scripts.

No external dependency is required for reading the .env file; we parse it
ourselves so the loaders/query scripts work as long as pandas + the database
drivers (mysql-connector-python, pymongo) are installed.
"""
from __future__ import annotations

import os
from pathlib import Path

# task3_database/ lives one level below the repo root.
TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parent
ENV_PATH = TASK_DIR / ".env"
CSV_PATH = REPO_ROOT / "clean_energy_dataset.csv"
SCHEMA_PATH = TASK_DIR / "schema.sql"

# Fixed metadata for the single region present in the PJME dataset.
REGION_CODE = "PJME"
REGION_NAME = "PJM East"
REGION_DESCRIPTION = "PJM Interconnection — Eastern hub hourly load (megawatts)"


def load_env(env_path: Path = ENV_PATH) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ (no overwrite)."""
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_mysql_config() -> dict:
    load_env()
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "energy_db"),
    }


RESULTS_PATH = TASK_DIR / "query_results.md"


def write_results_section(marker: str, content: str) -> None:
    """Replace the block between <!--marker--> and <!--/marker--> in query_results.md.

    Lets sql_queries.py and mongo_queries.py each drop their captured output into
    the shared results file without clobbering the other's section.
    """
    start = f"<!--{marker}-->"
    end = f"<!--/{marker}-->"
    text = RESULTS_PATH.read_text()
    if start in text and end in text:
        before = text.split(start)[0]
        after = text.split(end)[1]
        RESULTS_PATH.write_text(f"{before}{start}\n{content}\n{end}{after}")
    else:  # markers missing — just append
        RESULTS_PATH.write_text(f"{text}\n{start}\n{content}\n{end}\n")


def get_mongo_config() -> dict:
    load_env()
    return {
        "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        "db_name": os.getenv("MONGO_DB_NAME", "energy_db"),
        "collection": os.getenv("MONGO_COLLECTION", "energy_readings"),
    }
