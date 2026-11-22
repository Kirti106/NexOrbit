## NexOrbit

Satellite tracking, orbital analysis, SOCRATES-derived conjunction screening and sustainability analytics.

```
Browser (React + Cesium, :5173)  ->  Backend (FastAPI, :8000, /api/*)  ->  ML API (FastAPI, :8001)  ->  PostgreSQL/PostGIS
```

The backend is a thin proxy: it never recomputes ML output, so every response keeps
`model_version`, `generated_at`, `risk_tier`, `is_artifact` and `basis`.

### Run everything

```powershell
Copy-Item .env.example .env            # set POSTGRES_PASSWORD
docker compose up --build -d           # postgres :5432, ml_api :8001, backend :8000
# first time only: apply migrations + load data, see ml/HANDOVER.md section 2
docker compose restart ml_api

cd frontend
Copy-Item .env.example .env            # add VITE_CESIUM_ION_TOKEN (optional, see below)
npm install
npm run dev                            # http://localhost:5173
```

Check: http://localhost:8000/api/health and http://localhost:8000/docs

### Frontend data sources

| Page | Endpoint(s) |
|---|---|
| Overview | `/api/stats` |
| Tracking | `/api/satellites?q=&type=`, `/api/satellites/{id}/position` |
| Orbit Map | `/api/satellites/live` (every 30 s), `/api/satellites/{id}/ground-track` |
| Alerts | `/api/conjunctions?risk=` (high, medium, low) |
| Analytics | `/api/stats`, `/api/satellites/live`, `/api/anomalies` |

Without `VITE_CESIUM_ION_TOKEN` the globe falls back to OpenStreetMap imagery.
The ML API can also be used directly (same routes, no `/api` prefix), but the frontend is configured for the backend.

ML details: [ml/HANDOVER.md](ml/HANDOVER.md)
