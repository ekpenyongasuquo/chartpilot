import sqlite3
import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIT_DB_PATH = os.path.join(_BACKEND_DIR, "..", "demo_data", "chartpilot_demo.db")


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def log_access(
    doctor_id: str,
    query_text: str,
    patient_ids_accessed: list,
    record_count: int,
    sql_executed: Optional[str] = None,
    flagged: bool = False,
) -> None:
    if not _audit_enabled():
        return
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT NOT NULL,
                doctor_id       TEXT NOT NULL,
                query_hash      TEXT NOT NULL,
                patients_accessed TEXT,
                record_count    INTEGER,
                sql_hash        TEXT,
                critical_flagged INTEGER DEFAULT 0,
                access_purpose  TEXT DEFAULT 'clinical_query'
            )
        """)
        patient_list = ",".join(patient_ids_accessed) if patient_ids_accessed else ""
        sql_hash = hashlib.sha256(sql_executed.encode()).hexdigest()[:16] if sql_executed else ""
        conn.execute("""
            INSERT INTO audit_log
            (timestamp, doctor_id, query_hash, patients_accessed,
             record_count, sql_hash, critical_flagged)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            doctor_id,
            _hash_query(query_text),
            patient_list,
            record_count,
            sql_hash,
            1 if flagged else 0,
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Audit log write failed: {e}")


def _audit_enabled() -> bool:
    return os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"