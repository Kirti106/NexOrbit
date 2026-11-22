import os

# Base URL of the ML service (FastAPI, ml/src/api/app.py).
# Inside docker compose this is http://ml_api:8001.
ML_API_URL = os.getenv("ML_API_URL", "http://localhost:8001").rstrip("/")

# Seconds to wait for the ML service before answering 502/504.
ML_API_TIMEOUT = float(os.getenv("ML_API_TIMEOUT", "20"))

# React/Vite development server(s), comma separated.
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
