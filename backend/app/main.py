from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401 - registers SQLAlchemy models
from .config import get_settings
from .database import Base, engine
from .routers import analytics, conjunctions, satellites

Base.metadata.create_all(bind=engine)
settings = get_settings()

app = FastAPI(
    title="NexOrbit API",
    description=(
        "Space traffic intelligence prototype: satellite catalogue ingestion, "
        "TLE storage and SGP4 position propagation."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(satellites.router)
app.include_router(analytics.router)
app.include_router(conjunctions.router)


@app.get("/", tags=["System"])
def home():
    return {
        "project": "NexOrbit",
        "message": "NexOrbit API is running",
        "status": "running",
    }


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "healthy", "project": "NexOrbit"}
