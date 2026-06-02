# ChartPilot 🩺

> **License: MIT** · Track 4: Autopilot Agent · Global AI Hackathon with Qwen Cloud

**ChartPilot** is an autonomous clinical record retrieval agent that gives Nigerian Federal Medical Centre doctors instant, conversational access to patient records during consultations — powered by Qwen-Max on Alibaba Cloud.

---

## The Problem

Nigerian Federal Medical Centres have HMIS software — but doctors can't retrieve patient results fast enough during consultations. Finding a lab result takes 2–4 minutes of HMIS navigation. Doctors re-order tests, delay decisions, or skip the software entirely.

**ChartPilot fills the gap:** a zero-new-infrastructure agent layer that makes existing HMIS data conversationally accessible in under 5 seconds.

---

## Demo

> _"Show me Emeka's last two malaria RDT results"_
> _"What was the BP trend for patient 00451 in the last 3 visits?"_
> _"Any pending lab results for patients I admitted yesterday?"_

ChartPilot parses the query → translates to safe read-only SQL → retrieves results → flags critical values → returns a clean clinical summary.

---

## Architecture

```
Doctor's Browser
      ↓
ChartPilot Frontend (React)
      ↓
FastAPI Backend (Alibaba Cloud ECS)
      ↓          ↓
Qwen-Max     HMIS DB Adapter
(DashScope)  (PostgreSQL/SQLite)
      ↓          ↓
  Structured Query Engine (ApsaraDB RDS)
      ↓
Result Formatter + Flag Engine
(Critical values · NDPR audit log)
      ↓
Doctor's Screen (< 5 seconds)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language Model | Qwen-Max via DashScope API |
| Backend | FastAPI (Python 3.11) |
| Database | SQLite (dev) / ApsaraDB RDS (prod) |
| Frontend | React + Vite |
| Cloud | Alibaba Cloud ECS + Function Compute |
| Compliance | NDPR audit logging |

---

## Project Structure

```
chartpilot/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── qwen_agent.py        # Qwen intent parsing + summarization
│   ├── query_engine.py      # NL → safe read-only SQL
│   ├── hmis_adapter.py      # Database connector + schema loader
│   ├── flag_engine.py       # Critical value detection
│   ├── audit_logger.py      # NDPR-compliant access logging
│   └── models.py            # Pydantic request/response models
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       └── index.css
├── demo_data/
│   ├── seed_db.py           # Seeds SQLite with realistic Nigerian patient records
│   └── chartpilot_demo.db   # Auto-generated demo database
├── docs/
│   └── architecture.md
├── requirements.txt
├── .env.example
├── LICENSE                  # MIT
└── README.md
```

---

## Quick Start (Local Development)

### 1. Clone and install

```bash
git clone https://github.com/ekpenyongasuquo/chartpilot.git
cd chartpilot
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
cp .env.example .env
# Edit .env and add your DASHSCOPE_API_KEY
```

### 3. Seed the demo database

```bash
cd demo_data
python seed_db.py
```

### 4. Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Alibaba Cloud Deployment

See `docs/alibaba_deployment.md` for step-by-step ECS + ApsaraDB RDS deployment instructions.

The backend is deployed at: `https://chartpilot.[your-ecs-ip].nip.io`

---

## NDPR Compliance

All patient record access is logged with:
- Timestamp
- Doctor user ID
- Query text (hashed)
- Records accessed (patient ID only)
- Access purpose flag

Logs are stored in a separate audit table and never returned to the frontend.

---

## Human-in-the-Loop

Any query that would modify patient data triggers a confirmation gate before execution. Read-only queries are never blocked.

---

## Built By

**Ekpenyong Asuquo** — Developer & Statistician  
Federal Medical Centre, Calabar, Cross River State, Nigeria  
GitHub: [@ekpenyongasuquo](https://github.com/ekpenyongasuquo)
