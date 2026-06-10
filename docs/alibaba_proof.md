# Alibaba Cloud Deployment Proof

## ChartPilot — Live on Alibaba Cloud ECS

### Instance Details
- **Service:** ChartPilot FastAPI Backend
- **Region:** Singapore (ap-southeast-1)
- **Instance:** ecs.t5-lc1m2.small
- **Public IP:** 47.84.226.6
- **Status:** Running

### Alibaba Cloud Services Used
- **ECS:** Backend hosting — instance i-t4n44gbij7605r5f9htm
- **DashScope International API:** Qwen-Max model access
- **ApsaraDB RDS:** Production database (SQLite in demo)

### Live Endpoints
- Health: http://47.84.226.6:8000/health
- API Docs: http://47.84.226.6:8000/docs
- Query: http://47.84.226.6:8000/query

### Verification
Health check returns:
{"status":"ok","version":"1.0.0","db_connected":true,"qwen_connected":true}
