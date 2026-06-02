"""
flag_engine.py — Critical value detection for ChartPilot

Scans query results for clinically dangerous values and raises flags.
Based on standard Nigerian FMC reference ranges.

Flags are surfaced to the doctor in the UI with ⚠️ WARNING or 🚨 CRITICAL indicators.
"""
from models import CriticalFlag
from typing import List

# ── Critical value thresholds (Nigerian FMC reference ranges) ───────────────

CRITICAL_RULES = [
    # Haematology
    {
        "fields": ["haemoglobin", "hb", "hemoglobin"],
        "unit_hint": "g/dl",
        "critical_low": 7.0,
        "warning_low": 10.0,
        "critical_high": None,
        "warning_high": None,
        "label": "Haemoglobin",
    },
    {
        "fields": ["pcv", "packed cell volume", "haematocrit"],
        "unit_hint": "%",
        "critical_low": 21.0,
        "warning_low": 30.0,
        "critical_high": None,
        "warning_high": None,
        "label": "PCV",
    },
    # Metabolic
    {
        "fields": ["glucose", "blood glucose", "fbs", "rbs"],
        "unit_hint": "mmol/l",
        "critical_low": 2.5,
        "warning_low": 3.9,
        "critical_high": 22.2,
        "warning_high": 11.1,
        "label": "Blood Glucose",
    },
    {
        "fields": ["hba1c", "glycated haemoglobin"],
        "unit_hint": "%",
        "critical_low": None,
        "warning_low": None,
        "critical_high": 10.0,
        "warning_high": 7.0,
        "label": "HbA1c",
    },
    # Vitals
    {
        "fields": ["bp_systolic", "systolic"],
        "unit_hint": "mmhg",
        "critical_low": 80,
        "warning_low": 90,
        "critical_high": 180,
        "warning_high": 160,
        "label": "Systolic BP",
    },
    {
        "fields": ["bp_diastolic", "diastolic"],
        "unit_hint": "mmhg",
        "critical_low": 50,
        "warning_low": 60,
        "critical_high": 120,
        "warning_high": 100,
        "label": "Diastolic BP",
    },
    {
        "fields": ["spo2", "oxygen saturation"],
        "unit_hint": "%",
        "critical_low": 90,
        "warning_low": 94,
        "critical_high": None,
        "warning_high": None,
        "label": "SpO2",
    },
    # Renal
    {
        "fields": ["creatinine", "serum creatinine"],
        "unit_hint": "umol/l",
        "critical_low": None,
        "warning_low": None,
        "critical_high": 500,
        "warning_high": 133,
        "label": "Serum Creatinine",
    },
    {
        "fields": ["potassium", "k+"],
        "unit_hint": "mmol/l",
        "critical_low": 2.5,
        "warning_low": 3.5,
        "critical_high": 6.5,
        "warning_high": 5.5,
        "label": "Potassium (K+)",
    },
    # Malaria
    {
        "fields": ["malaria rdt", "rdt", "malaria"],
        "unit_hint": None,
        "text_critical": ["positive", "+ve"],
        "label": "Malaria RDT",
    },
]


def _extract_numeric(value_str: str) -> float | None:
    """Extract numeric value from a result string like '4.2 g/dL' or '120'."""
    try:
        return float("".join(c for c in str(value_str) if c.isdigit() or c == ".").strip())
    except (ValueError, AttributeError):
        return None


def scan_for_critical_values(records: List[dict]) -> List[CriticalFlag]:
    """
    Scan a list of HMIS result records for clinically critical values.
    Returns a list of CriticalFlag objects.
    """
    flags: List[CriticalFlag] = []

    for record in records:
        for key, value in record.items():
            if value is None:
                continue

            key_lower = str(key).lower()
            value_str = str(value).lower()

            for rule in CRITICAL_RULES:
                # Check if this record field matches this rule
                matched = any(field in key_lower for field in rule["fields"])
                if not matched:
                    continue

                # Text-based rules (e.g. Malaria RDT positive)
                if "text_critical" in rule:
                    if any(t in value_str for t in rule["text_critical"]):
                        flags.append(CriticalFlag(
                            field=rule["label"],
                            value=str(value),
                            threshold="Positive result",
                            severity="CRITICAL",
                            message=f"🚨 {rule['label']}: POSITIVE — treatment required",
                        ))
                    continue

                # Numeric rules
                numeric = _extract_numeric(value_str)
                if numeric is None:
                    continue

                if rule.get("critical_low") and numeric < rule["critical_low"]:
                    flags.append(CriticalFlag(
                        field=rule["label"],
                        value=f"{numeric} {rule.get('unit_hint', '')}",
                        threshold=f"< {rule['critical_low']} {rule.get('unit_hint', '')}",
                        severity="CRITICAL",
                        message=f"🚨 {rule['label']} critically low: {numeric}",
                    ))
                elif rule.get("warning_low") and numeric < rule["warning_low"]:
                    flags.append(CriticalFlag(
                        field=rule["label"],
                        value=f"{numeric} {rule.get('unit_hint', '')}",
                        threshold=f"< {rule['warning_low']} {rule.get('unit_hint', '')}",
                        severity="WARNING",
                        message=f"⚠️ {rule['label']} below normal: {numeric}",
                    ))
                elif rule.get("critical_high") and numeric > rule["critical_high"]:
                    flags.append(CriticalFlag(
                        field=rule["label"],
                        value=f"{numeric} {rule.get('unit_hint', '')}",
                        threshold=f"> {rule['critical_high']} {rule.get('unit_hint', '')}",
                        severity="CRITICAL",
                        message=f"🚨 {rule['label']} critically high: {numeric}",
                    ))
                elif rule.get("warning_high") and numeric > rule["warning_high"]:
                    flags.append(CriticalFlag(
                        field=rule["label"],
                        value=f"{numeric} {rule.get('unit_hint', '')}",
                        threshold=f"> {rule['warning_high']} {rule.get('unit_hint', '')}",
                        severity="WARNING",
                        message=f"⚠️ {rule['label']} above normal: {numeric}",
                    ))

    return flags