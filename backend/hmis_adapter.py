"""
hmis_adapter.py — Read-only HMIS database connector for ChartPilot

Connects to the hospital's existing database (SQLite for demo, 
ApsaraDB RDS PostgreSQL for production) and exposes:
  - Schema introspection (so Qwen understands what tables exist)
  - Safe read-only query execution
  - Patient search by partial name / ID
"""
import os
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(_BACKEND_DIR, "..", "demo_data", "chartpilot_demo.db"))

# ── Schema exposed to Qwen so it can generate accurate SQL ──────────────────

HMIS_SCHEMA_DESCRIPTION = """
You have access to a Nigerian Federal Medical Centre HMIS database with these tables:

TABLE: patients
  - patient_id     TEXT PRIMARY KEY  (e.g. "FMC-00451")
  - first_name     TEXT
  - last_name      TEXT
  - date_of_birth  TEXT  (YYYY-MM-DD)
  - gender         TEXT  (M/F)
  - phone          TEXT
  - address        TEXT
  - blood_group    TEXT

TABLE: visits
  - visit_id       TEXT PRIMARY KEY
  - patient_id     TEXT  (FK → patients)
  - visit_date     TEXT  (YYYY-MM-DD)
  - doctor_id      TEXT
  - department     TEXT  (e.g. "General OPD", "ANC", "Paediatrics")
  - complaint      TEXT
  - diagnosis      TEXT
  - notes          TEXT

TABLE: lab_results
  - result_id      TEXT PRIMARY KEY
  - patient_id     TEXT  (FK → patients)
  - visit_id       TEXT  (FK → visits)
  - test_name      TEXT  (e.g. "Malaria RDT", "FBC", "HbA1c", "Urinalysis")
  - result_value   TEXT
  - result_unit    TEXT
  - reference_range TEXT
  - status         TEXT  (PENDING/COMPLETED/CRITICAL)
  - collected_date TEXT  (YYYY-MM-DD)
  - reported_date  TEXT  (YYYY-MM-DD)

TABLE: vitals
  - vital_id       TEXT PRIMARY KEY
  - patient_id     TEXT  (FK → patients)
  - visit_id       TEXT  (FK → visits)
  - recorded_date  TEXT  (YYYY-MM-DD)
  - bp_systolic    INTEGER   (mmHg)
  - bp_diastolic   INTEGER   (mmHg)
  - pulse          INTEGER   (bpm)
  - temperature    REAL      (°C)
  - weight_kg      REAL
  - height_cm      REAL
  - spo2           INTEGER   (%)

TABLE: medications
  - med_id         TEXT PRIMARY KEY
  - patient_id     TEXT  (FK → patients)
  - visit_id       TEXT  (FK → visits)
  - drug_name      TEXT
  - dosage         TEXT
  - frequency      TEXT
  - start_date     TEXT  (YYYY-MM-DD)
  - end_date       TEXT  (YYYY-MM-DD)
  - prescribed_by  TEXT  (doctor_id)

RULES FOR QUERY GENERATION:
- ONLY generate SELECT statements. Never INSERT, UPDATE, DELETE, DROP, or ALTER.
- Use LIKE with % for partial name matching (e.g. WHERE first_name LIKE '%Emeka%')
- Always LIMIT results to 20 unless the doctor asks for more
- For "last N results" use ORDER BY date DESC LIMIT N
- patient_id format is FMC-XXXXX (e.g. FMC-00451)
- Dates are stored as TEXT in YYYY-MM-DD format
"""


def get_connection() -> sqlite3.Connection:
    """Get a read-only SQLite connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def execute_safe_query(sql: str) -> list[dict]:
    """
    Execute a read-only SQL query and return results as list of dicts.
    Raises ValueError if query contains write operations.
    """
    # Safety check — block any write operations
    forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]
    sql_lower = sql.lower().strip()
    for word in forbidden:
        if f" {word} " in f" {sql_lower} " or sql_lower.startswith(word):
            raise ValueError(f"Write operation '{word}' is not permitted. ChartPilot is read-only.")

    try:
        conn = get_connection()
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except sqlite3.OperationalError as e:
        logger.error(f"SQL execution error: {e} | SQL: {sql}")
        raise ValueError(f"Database query failed: {str(e)}")


def search_patient_by_name(partial_name: str) -> list[dict]:
    """
    Fuzzy patient name search — used when Qwen identifies a name 
    but doesn't have the exact patient_id.
    """
    sql = f"""
        SELECT patient_id, first_name, last_name, date_of_birth, gender
        FROM patients
        WHERE first_name LIKE '%{partial_name}%'
           OR last_name LIKE '%{partial_name}%'
        LIMIT 10
    """
    return execute_safe_query(sql)


def get_db_status() -> bool:
    """Check if the database file exists and is accessible."""
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False