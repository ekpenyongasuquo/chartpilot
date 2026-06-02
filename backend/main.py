import sys
import os

# Force Python to find sibling modules in the same directory
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import time
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import QueryRequest, QueryResult, ConfirmationRequest, HealthResponse
from chartpilot_qwen import parse_query_intent, summarize_results, check_qwen_connection
from hmis_adapter import execute_safe_query, search_patient_by_name, get_db_status
from flag_engine import scan_for_critical_values
from audit_logger import log_access

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory store for pending confirmations (human-in-the-loop)
pending_confirmations: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ChartPilot backend starting...")
    logger.info(f"DB status: {'OK' if get_db_status() else 'FAIL — run demo_data/seed_db.py'}")
    logger.info(f"Qwen status: {'OK' if check_qwen_connection() else 'FAIL — check DASHSCOPE_API_KEY'}")
    yield
    logger.info("ChartPilot backend shutting down.")


app = FastAPI(
    title="ChartPilot API",
    description="Autonomous clinical record retrieval agent for Nigerian Federal Medical Centres",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        db_connected=get_db_status(),
        qwen_connected=check_qwen_connection(),
    )


@app.post("/query", response_model=QueryResult)
async def process_query(request: QueryRequest):
    start_time = time.time()
    logger.info(f"Query from doctor {request.doctor_id}: {request.query[:80]}")

    # Step 1: Parse intent with Qwen
    try:
        intent = parse_query_intent(request.query)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qwen API unavailable: {str(e)}")

    understood_as = intent.get("understood_as", "Query not understood")
    sql = intent.get("sql")
    requires_confirmation = intent.get("requires_confirmation", False)
    confirmation_reason = intent.get("confirmation_reason")

    # Step 2: Human-in-the-loop gate
    if requires_confirmation:
        session_id = f"confirm_{request.doctor_id}_{int(time.time())}"
        pending_confirmations[session_id] = {
            "sql": sql,
            "doctor_id": request.doctor_id,
            "query": request.query,
        }
        return QueryResult(
            success=True,
            query_interpreted=understood_as,
            summary=f"This action requires confirmation: {confirmation_reason}",
            requires_confirmation=True,
            confirmation_action=session_id,
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    # Step 3: Handle ambiguous query
    if not sql:
        return QueryResult(
            success=False,
            query_interpreted=understood_as,
            summary="Query was too ambiguous. Please provide a patient name, ID, or specific test name.",
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    # Step 4: Patient name resolution
    name_hint = intent.get("patient_name_hint")
    if name_hint:
        name_matches = search_patient_by_name(name_hint)
        if len(name_matches) == 1:
            patient_id = name_matches[0]["patient_id"]
            sql = sql.replace(f"LIKE '%{name_hint}%'", f"= '{patient_id}'")
        elif len(name_matches) > 1:
            names = [f"{r['first_name']} {r['last_name']} ({r['patient_id']})" for r in name_matches]
            return QueryResult(
                success=True,
                query_interpreted=understood_as,
                summary=f"Multiple patients match '{name_hint}'. Please specify:\n" + "\n".join(names),
                records=name_matches,
                record_count=len(name_matches),
                response_time_ms=int((time.time() - start_time) * 1000),
            )

    # Step 5: Execute safe read-only SQL
    try:
        records = execute_safe_query(sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 6: Scan for critical values
    critical_flags = scan_for_critical_values(records)

    # Step 7: Summarize with Qwen
    summary = summarize_results(request.query, records, understood_as)

    # Step 8: NDPR audit log
    patient_ids = list(set(
        str(r.get("patient_id", "")) for r in records if r.get("patient_id")
    ))
    log_access(
        doctor_id=request.doctor_id,
        query_text=request.query,
        patient_ids_accessed=patient_ids,
        record_count=len(records),
        sql_executed=sql,
        flagged=len(critical_flags) > 0,
    )

    response_time = int((time.time() - start_time) * 1000)
    logger.info(f"Query completed in {response_time}ms — {len(records)} records, {len(critical_flags)} flags")

    return QueryResult(
        success=True,
        query_interpreted=understood_as,
        sql_executed=sql if os.getenv("APP_ENV") == "development" else None,
        summary=summary,
        records=records,
        critical_flags=critical_flags,
        record_count=len(records),
        response_time_ms=response_time,
    )


@app.post("/confirm", response_model=QueryResult)
async def confirm_action(request: ConfirmationRequest):
    pending = pending_confirmations.get(request.session_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Confirmation session not found or expired.")
    if pending["doctor_id"] != request.doctor_id:
        raise HTTPException(status_code=403, detail="Confirmation session belongs to a different doctor.")

    del pending_confirmations[request.session_id]

    if not request.confirmed:
        return QueryResult(
            success=True,
            query_interpreted="Action cancelled by doctor",
            summary="Action was cancelled. No changes were made.",
        )

    sql = pending["sql"]
    try:
        records = execute_safe_query(sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    critical_flags = scan_for_critical_values(records)
    summary = summarize_results(pending["query"], records, "Confirmed action")

    log_access(
        doctor_id=request.doctor_id,
        query_text=pending["query"],
        patient_ids_accessed=[str(r.get("patient_id", "")) for r in records],
        record_count=len(records),
        sql_executed=sql,
        flagged=len(critical_flags) > 0,
    )

    return QueryResult(
        success=True,
        query_interpreted="Confirmed action executed",
        summary=summary,
        records=records,
        critical_flags=critical_flags,
        record_count=len(records),
    )