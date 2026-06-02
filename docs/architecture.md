# ChartPilot — System Architecture

## Overview

ChartPilot is a Track 4 Autopilot Agent that adds a conversational retrieval layer on top of existing Nigerian Federal Medical Centre HMIS databases. No new infrastructure is required at the hospital — ChartPilot connects to whatever database the hospital already runs.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCTOR'S BROWSER / TABLET                │
│                                                             │
│   "Show me Emeka's last two malaria RDT results"            │
│                        │                                    │
│              ChartPilot Frontend (React + Vite)             │
│              Dark clinical UI · Demo mode fallback          │
└─────────────────────────────┬───────────────────────────────┘
                              │  POST /query
                              │  { query, doctor_id }
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND  ── Alibaba Cloud ECS          │
│                                                             │
│   main.py                                                   │
│   ├── Receives NL query                                     │
│   ├── Calls Qwen-Max for intent parsing                     │
│   ├── Runs safe read-only SQL via HMIS adapter              │
│   ├── Scans results through flag engine                     │
│   ├── Calls Qwen-Max for clinical summarization             │
│   ├── Writes NDPR audit log                                 │
│   └── Returns structured response to frontend              │
│                                                             │
│   Human-in-the-loop gate:                                   │
│   Any data-modifying action → confirmation required         │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────┐    ┌─────────────────────────────────┐
│   QWEN-MAX API       │    │   HMIS DATABASE ADAPTER         │
│   (DashScope)        │    │                                 │
│                      │    │   hmis_adapter.py               │
│   1. Parse intent    │    │   ├── Schema introspection      │
│      → structured    │    │   ├── Partial name resolution   │
│        JSON + SQL    │    │   └── Read-only connector       │
│                      │    │                                 │
│   2. Summarize       │    │   Supports:                     │
│      raw records     │    │   · SQLite (dev/demo)           │
│      → clinical      │    │   · PostgreSQL (production)     │
│        summary       │    │   · MySQL                       │
│                      │    │   · ApsaraDB RDS (Alibaba)      │
└──────────┬───────────┘    └──────────────┬──────────────────┘
           │                               │
           └──────────────┬────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STRUCTURED QUERY ENGINE                        │
│                                                             │
│   query_engine.py (logic in hmis_adapter.py)               │
│   ├── Translates Qwen intent JSON → safe SELECT SQL         │
│   ├── Blocks all write operations (INSERT/UPDATE/DELETE)    │
│   ├── Patient name disambiguation (partial → patient_id)   │
│   └── Result pagination and limiting                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         RESULT FORMATTER + FLAG ENGINE                      │
│                                                             │
│   flag_engine.py                                            │
│   ├── Critical value thresholds (Nigerian FMC ranges)       │
│   │   · Haemoglobin < 7.0 g/dL → 🚨 CRITICAL              │
│   │   · Malaria RDT Positive   → 🚨 CRITICAL               │
│   │   · BP Systolic > 180 mmHg → 🚨 CRITICAL               │
│   │   · Blood Glucose > 22.2   → 🚨 CRITICAL               │
│   │   · SpO2 < 90%             → 🚨 CRITICAL               │
│   │   + 6 more rules                                        │
│   └── Returns CriticalFlag list with severity levels        │
│                                                             │
│   audit_logger.py (NDPR Compliance)                         │
│   ├── Timestamp of access                                   │
│   ├── Doctor ID                                             │
│   ├── Query hash (SHA-256, not raw text)                    │
│   ├── Patient IDs accessed                                  │
│   └── Critical flag indicator                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 DOCTOR'S SCREEN                             │
│                                                             │
│   Response includes:                                        │
│   ├── Clinical summary (Qwen-generated, < 100 words)        │
│   ├── Critical flags (🚨 CRITICAL / ⚠️ WARNING)            │
│   ├── Raw records (expandable table)                        │
│   ├── Query interpretation ("understood as...")             │
│   └── Response time (target: < 5 seconds)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Alibaba Cloud Services Used

| Service | Purpose |
|---|---|
| **ECS (Elastic Compute Service)** | FastAPI backend hosting |
| **ApsaraDB RDS (PostgreSQL)** | Production HMIS database |
| **DashScope API** | Qwen-Max model access (intent parsing + summarization) |
| **Function Compute** | Optional serverless query execution layer |

---

## Data Flow (Step by Step)

1. Doctor types natural language query into ChartPilot frontend
2. Frontend sends `POST /query` to FastAPI backend on Alibaba Cloud ECS
3. Backend sends query to **Qwen-Max** for intent parsing
4. Qwen returns structured JSON: `{ understood_as, sql, patient_name_hint }`
5. If query targets a patient by name, **HMIS adapter** resolves partial name → `patient_id`
6. **Query engine** executes safe read-only SQL against HMIS database
7. **Flag engine** scans results for critical clinical values
8. Backend calls **Qwen-Max** again to summarize raw records into clinical language
9. **NDPR audit logger** writes access record (non-blocking)
10. Response returned to doctor's screen in under 5 seconds

---

## Security Model

- **Read-only enforcement**: All write SQL keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`) are blocked at the adapter layer before any query reaches the database
- **Human-in-the-loop gate**: Any action flagged as data-modifying by Qwen returns `requires_confirmation: true` — doctor must explicitly confirm before execution
- **NDPR compliance**: All record access is logged with doctor ID, timestamp, patient IDs accessed, and query hash. Raw query text is never stored — only SHA-256 hash
- **No PII in summaries**: Qwen is instructed never to include patient names or IDs in clinical summaries

---

## Why Qwen-Max Specifically

| Capability | ChartPilot Use |
|---|---|
| Multilingual reasoning | Handles English, medical abbreviations, Nigerian Pidgin code-switching |
| Tool calling / function use | Maps directly to SQL generation step |
| Long context window | Full patient history fits in one summarization call |
| DashScope on Alibaba Cloud | Native integration — low latency, no cross-cloud overhead |

---

## Scalability Path

| Stage | Configuration |
|---|---|
| **Demo** | SQLite + single ECS instance |
| **Single hospital** | ApsaraDB RDS PostgreSQL + ECS |
| **Multi-facility** | RDS read replicas per facility + shared ECS cluster |
| **National rollout** | Alibaba Cloud CDN + regional ECS + federated RDS |

---

*ChartPilot — Built by Ekpenyong Asuquo · Federal Medical Centre, Calabar, Nigeria*
*Global AI Hackathon with Qwen Cloud · Track 4: Autopilot Agent*
