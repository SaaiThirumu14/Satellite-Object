from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import sqrt

from .data_structures import OpenAddressedHashSet, SkipListPriorityQueue


@dataclass(frozen=True)
class Vector3:
    x: float
    y: float
    z: float

    def subtract(self, other: Vector3) -> Vector3:
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def add_scaled(self, other: Vector3, factor: float) -> Vector3:
        return Vector3(self.x + other.x * factor, self.y + other.y * factor, self.z + other.z * factor)


@dataclass(frozen=True)
class Telemetry:
    object_id: str
    object_type: str
    timestamp: datetime
    position: Vector3
    velocity: Vector3


@dataclass(frozen=True)
class ConjunctionAlert:
    object1_id: str
    object2_id: str
    tca: datetime
    time_to_tca_seconds: float
    minimum_separation: float
    risk_level: str
    created_at: datetime
    status: str = "new"


def closest_approach(
    position1: Vector3,
    velocity1: Vector3,
    position2: Vector3,
    velocity2: Vector3,
    start_time: datetime,
    horizon_seconds: float,
) -> tuple[datetime, float, float]:
    relative_position = position1.subtract(position2)
    relative_velocity = velocity1.subtract(velocity2)
    speed_squared = _dot(relative_velocity, relative_velocity)
    if speed_squared == 0:
        seconds = 0.0
    else:
        unconstrained = -_dot(relative_position, relative_velocity) / speed_squared
        seconds = max(0.0, min(horizon_seconds, unconstrained))
    separation = _magnitude(relative_position.add_scaled(relative_velocity, seconds))
    return start_time + timedelta(seconds=seconds), separation, seconds


def risk_level(separation: float, threshold: float) -> str:
    ratio = separation / threshold
    if ratio <= 0.25:
        return "critical"
    if ratio <= 0.5:
        return "high"
    if ratio <= 1.0:
        return "medium"
    return "low"


def detect_conjunctions(
    telemetry: list[Telemetry],
    threshold: float,
    horizon_seconds: float,
    now: datetime | None = None,
) -> list[ConjunctionAlert]:
    if threshold <= 0 or horizon_seconds <= 0:
        raise ValueError("threshold and horizon_seconds must be positive")
    object_ids = OpenAddressedHashSet(max(4, len(telemetry) * 2))
    for item in telemetry:
        object_ids.add(item.object_id)
    created_at = now or datetime.now(timezone.utc)
    pairs = ((telemetry[first], telemetry[second])
             for first in range(len(telemetry))
             for second in range(first + 1, len(telemetry)))
    with ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda pair: _evaluate_pair(pair[0], pair[1], threshold, horizon_seconds, created_at), pairs
        )
        queue: SkipListPriorityQueue[ConjunctionAlert] = SkipListPriorityQueue()
        for alert in results:
            if alert is not None:
                queue.push(alert.time_to_tca_seconds, alert)
    alerts = []
    while queue:
        alerts.append(queue.pop())
    return alerts


def _evaluate_pair(first: Telemetry, second: Telemetry, threshold: float, horizon: float,
                   created_at: datetime) -> ConjunctionAlert | None:
    start = max(first.timestamp, second.timestamp)
    tca, separation, seconds = closest_approach(
        first.position, first.velocity, second.position, second.velocity, start, horizon
    )
    if separation > threshold:
        return None
    return ConjunctionAlert(
        first.object_id, second.object_id, tca, seconds, separation,
        risk_level(separation, threshold), created_at
    )


def _dot(left: Vector3, right: Vector3) -> float:
    return left.x * right.x + left.y * right.y + left.z * right.z


def _magnitude(vector: Vector3) -> float:
    return sqrt(_dot(vector, vector))

