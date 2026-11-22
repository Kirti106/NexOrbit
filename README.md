# NexOrbit

NexOrbit runs as a React frontend, a FastAPI backend, a PostgreSQL/PostGIS
database, and an orbital propagation/analytics API. The backend reads the
shared database; the sample datasets are loaded into that database once when
the Compose stack starts with an empty catalogue.

## Run the integrated application

From this directory:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
Set-Location frontend
npm install
npm run dev
```

Open the frontend at <http://localhost:5173>. Vite forwards `/api` requests to
the backend at port 8000. API documentation is available at
<http://localhost:8000/docs>; the propagation API is at
<http://localhost:8001/docs>.

The Compose stack initializes the catalogue schema, applies the ML database
migrations, then imports the checked-in SATCAT, GP, and SOCRATES samples from
`ml/data/samples`. Dataset loading is idempotent and skips tables that already
contain records. Use a fresh database volume if you need to repeat the initial
schema setup.

Set `POSTGRES_PASSWORD` to a private value before exposing the database beyond
your local machine. `CORS_ORIGINS` accepts a comma-separated list of frontend
origins.

## Frontend data

- Overview and analytics read counts from the backend.
- Tracking reads the SATCAT catalogue and latest GP orbital elements.
- The orbital map requests propagated positions from the ML API through the
  backend.
- Conjunction alerts display SOCRATES predictions and derived risk tiers;
  they are not observed collisions or validated collision probabilities.

See [ml/HANDOVER.md](ml/HANDOVER.md) for ML API details and data semantics.
