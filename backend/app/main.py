from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .algorithms import ConjunctionAlert, Telemetry, Vector3, detect_conjunctions
from .models import AlertResponse, DetectionRequest
from .repository import ConjunctionRepository, DatabaseUnavailable

app = FastAPI(title="Satellite Conjunction Avoidance Engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
repository = ConjunctionRepository()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/conjunctions", response_model=list[AlertResponse])
def create_conjunctions(request: DetectionRequest) -> list[ConjunctionAlert]:
    telemetry = [
        Telemetry(
            item.object_id, item.object_type, item.timestamp,
            Vector3(*item.position), Vector3(*item.velocity),
        )
        for item in request.telemetry
    ]
    alerts = detect_conjunctions(telemetry, request.threshold, request.horizon_seconds)
    try:
        repository.save_detection(telemetry, alerts)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return alerts


@app.get("/v1/alerts", response_model=list[AlertResponse])
def get_alerts(limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    try:
        return repository.list_alerts(limit)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

