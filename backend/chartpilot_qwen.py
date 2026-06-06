"""
chartpilot_qwen.py — Qwen-Max intent parsing and clinical summarization

Two responsibilities:
  1. parse_query_intent()  -> Understand doctor's NL query -> generate SQL
  2. summarize_results()   -> Turn raw DB rows -> clean clinical summary

Uses DashScope International API (OpenAI-compatible endpoint) with Qwen-Max model.
"""
import os
import sys
import json
import logging

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from openai import OpenAI
from hmis_adapter import HMIS_SCHEMA_DESCRIPTION

logger = logging.getLogger(__name__)

QWEN_MODEL = "qwen-max"


def _get_client() -> OpenAI:
    """Create a fresh OpenAI-compatible client pointing at DashScope International."""
    api_key = os.getenv("DASHSCOPE_API_KEY", "placeholder")
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )


# ── Intent Parsing ────────────────────────────────────────────────────────────

INTENT_SYSTEM_PROMPT = f"""You are ChartPilot's query interpreter for a Nigerian Federal Medical Centre HMIS.

Your job: Convert a doctor's natural language query into a safe, read-only SQL SELECT statement.

{HMIS_SCHEMA_DESCRIPTION}

IMPORTANT CONTEXT — Nigerian clinical language:
- Doctors may use abbreviations: RDT (Rapid Diagnostic Test), FBC (Full Blood Count),
  BP (Blood Pressure), ANC (Antenatal Care), OPD (Outpatient Department),
  Hb (Haemoglobin), PCV (Packed Cell Volume), USS (Ultrasound Scan)
- Doctors may refer to patients by first name only, nickname, or partial name
- "Last visit" = most recent visit_date
- "This week/month" = relative to today's date
- Nigerian Pidgin phrases should be interpreted clinically:
  "wetin be im last result" = "what is their latest result"
  "check am well well" = "show complete history"

RESPONSE FORMAT — You must respond with ONLY valid JSON, no markdown, no explanation:
{{
  "understood_as": "plain English restatement of what you understood",
  "sql": "SELECT ... (safe read-only SQL)",
  "patient_name_hint": "partial name if mentioned, else null",
  "requires_confirmation": false,
  "confirmation_reason": null
}}

If the query would require modifying data, set requires_confirmation to true and explain why.
If the query is too ambiguous to generate SQL, set sql to null and explain in understood_as.
"""


def parse_query_intent(query: str) -> dict:
    """
    Parse a doctor's natural language query into structured intent + SQL.
    Returns dict with keys: understood_as, sql, patient_name_hint,
                            requires_confirmation, confirmation_reason
    """
    try:
        response = _get_client().chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=600,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError as e:
        logger.error(f"Qwen returned non-JSON intent: {e}")
        return {
            "understood_as": "Could not interpret query — please rephrase",
            "sql": None,
            "patient_name_hint": None,
            "requires_confirmation": False,
            "confirmation_reason": None,
        }
    except Exception as e:
        logger.error(f"Qwen API error in parse_query_intent: {e}")
        raise


# ── Result Summarization ──────────────────────────────────────────────────────

SUMMARY_SYSTEM_PROMPT = """You are ChartPilot's clinical summarizer for a Nigerian Federal Medical Centre.

Given raw database records and the original query, produce a concise, clinically useful summary
that a busy doctor can read in 10 seconds.

RULES:
- Lead with the most clinically relevant finding
- Use standard medical abbreviations (BP, Hb, RDT, etc.)
- Flag any abnormal values with ⚠️
- Flag any critical values with 🚨
- If no records found, say clearly: "No records found for [what was searched]"
- Keep summary under 100 words
- Do NOT include patient identifiers (name/ID) in the summary for NDPR compliance
- Format dates as DD-Mon-YYYY (e.g. 14-Jan-2026)

Respond with ONLY the summary text. No preamble, no JSON.
"""


def summarize_results(query: str, records: list, understood_as: str) -> str:
    """
    Generate a concise clinical summary from raw HMIS records.
    """
    if not records:
        return f"No records found. Query interpreted as: {understood_as}"

    try:
        records_text = json.dumps(records, indent=2, default=str)

        response = _get_client().chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Original query: {query}\nInterpreted as: {understood_as}\n\nRaw records:\n{records_text}"
                },
            ],
            temperature=0.3,
            max_tokens=200,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Qwen API error in summarize_results: {e}")
        return f"Retrieved {len(records)} record(s). Summary unavailable — please review raw data."


def check_qwen_connection() -> bool:
    """Ping Qwen API to verify connectivity."""
    try:
        _get_client().chat.completions.create(
            model=QWEN_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return True
    except Exception:
        return False