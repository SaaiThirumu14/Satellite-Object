from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TelemetryInput(BaseModel):
    object_id: str = Field(min_length=1, max_length=128)
    object_type: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    position: list[float] = Field(min_length=3, max_length=3)
    velocity: list[float] = Field(min_length=3, max_length=3)

    @field_validator("position", "velocity")
    @classmethod
    def finite_vector(cls, values: list[float]) -> list[float]:
        if any(value != value or value in (float("inf"), float("-inf")) for value in values):
            raise ValueError("vector values must be finite")
        return values


class DetectionRequest(BaseModel):
    telemetry: list[TelemetryInput] = Field(max_length=10_000)
    threshold: float = Field(gt=0)
    horizon_seconds: float = Field(gt=0, le=86_400)


class AlertResponse(BaseModel):
    object1_id: str
    object2_id: str
    tca: datetime
    time_to_tca_seconds: float
    minimum_separation: float
    risk_level: str
    created_at: datetime
    status: str

