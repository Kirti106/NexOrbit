from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_ORIGINS, ML_API_URL
from .routers import ml
from .services.ml_client import close_client, ml_get


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_client()


app = FastAPI(
    title="NexOrbit API",
    description=(
        "Backend for the NexOrbit dashboard. Proxies the ML service "
        "(satellite positions, SOCRATES-derived conjunction tiers, stats)."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(ml.router)


@app.get("/", tags=["System"])
def home():
    return {"project": "NexOrbit", "message": "NexOrbit API is running", "status": "running"}


@app.get("/api/health", tags=["System"])
async def health():
    """Backend health plus ML API/database status. Always answers 200."""
    try:
        upstream = await ml_get("/health")
        ml_status = upstream.get("status", "unknown")
        database = upstream.get("database", "unknown")
    except Exception:
        ml_status, database = "unreachable", "unknown"
    return {
        "status": "healthy" if ml_status == "healthy" else "degraded",
        "project": "NexOrbit",
        "ml_api": ml_status,
        "ml_api_url": ML_API_URL,
        "database": database,
    }
