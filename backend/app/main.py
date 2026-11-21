
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NexOrbit API",
    description="AI-Powered Space Traffic Intelligence & Orbital Sustainability Platform",
    version="1.0.0"
)

# Allow our React frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to NexOrbit!",
        "status": "running"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "project": "NexOrbit"
    }


@app.get("/api/analytics")
def analytics():
    return {
        "total_objects": 0,
        "active_satellites": 0,
        "debris_objects": 0,
        "upcoming_conjunctions": 0,
        "message": "Orbital datasets are not connected yet."
    }


@app.get("/api/satellites")
def satellites():
    return {
        "satellites": [],
        "message": "Satellite data will be added soon."
    }