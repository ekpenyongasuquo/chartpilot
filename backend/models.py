"""
models.py — Pydantic request/response models for ChartPilot
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class QueryRequest(BaseModel):
    query: str                          # Doctor's natural language query
    doctor_id: str                      # For NDPR audit logging
    session_id: Optional[str] = None    # For multi-turn context


class CriticalFlag(BaseModel):
    field: str          # e.g. "Haemoglobin"
    value: str          # e.g. "4.2 g/dL"
    threshold: str      # e.g. "< 7.0 g/dL"
    severity: str       # "WARNING" | "CRITICAL"
    message: str        # Human-readable flag message


class QueryResult(BaseModel):
    success: bool
    query_interpreted: str              # What ChartPilot understood
    sql_executed: Optional[str] = None  # For transparency (dev mode)
    summary: str                        # Qwen-generated clinical summary
    records: List[dict] = []            # Raw records (structured)
    critical_flags: List[CriticalFlag] = []
    record_count: int = 0
    response_time_ms: Optional[int] = None
    requires_confirmation: bool = False  # Human-in-the-loop gate
    confirmation_action: Optional[str] = None


class ConfirmationRequest(BaseModel):
    session_id: str
    doctor_id: str
    confirmed: bool


class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool
    qwen_connected: bool