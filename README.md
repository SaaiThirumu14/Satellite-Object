# Satellite Conjunction Detection Engine

This repository is a simulation-based research prototype for detecting close approaches between tracked orbital objects. It is not flight software and must not be used as the sole basis for maneuver decisions.

## Python, React, and PostgreSQL quick start

Requires Docker Desktop. The application is split into `backend` (FastAPI)
and `frontend` (React + Vite).

```powershell
docker compose up --build
```

This starts PostgreSQL with PostGIS, the Python API, and the React dashboard.
PostgreSQL listens on `5432`, the API on `8000`, and the dashboard on `5173`.
The first database startup runs
`db/migrations/001_init.sql`.

Open http://localhost:5173 to use the web interface. For a local backend run:

```powershell
docker compose up -d postgres
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

The API reads `DATABASE_URL`; its default points to the local Docker database.

The API exposes `GET /health` and `POST /v1/conjunctions`. A request contains telemetry records plus a distance threshold and prediction horizon:

```json
{
  "threshold": 2.0,
  "horizon_seconds": 3600,
  "telemetry": [
    {
      "object_id": "SAT-1",
      "object_type": "satellite",
      "timestamp": "2026-01-01T00:00:00Z",
      "position": [0, 0, 0],
      "velocity": [1, 0, 0]
    },
    {
      "object_id": "DEB-1",
      "object_type": "debris",
      "timestamp": "2026-01-01T00:00:00Z",
      "position": [5, 0, 0],
      "velocity": [-1, 0, 0]
    }
  ]
}
```

The implementation uses a constant-relative-velocity model, concurrent pair
evaluation, an open-addressed satellite ID index, and an unbounded randomized
skip-list priority queue. PostgreSQL/PostGIS stores telemetry, conjunction
alerts, and manoeuvre-log records. Keplerian/SGP4 propagation, uncertainty
modeling, and operational safety controls remain future integrations.

## Mini-project overview

This project is a simulation-based **Satellite Conjunction Detection Engine**.
It examines telemetry from satellites and orbital debris to identify pairs that
may come within a configured distance threshold during a future prediction
horizon. A conjunction alert contains the two object IDs, time of closest
approach (TCA), predicted minimum separation, risk level, and status.

This is a research prototype and not flight-control software. It must not be
used as the sole basis for real spacecraft manoeuvre decisions.

## System flow

```text
React dashboard
    ↓
POST /v1/conjunctions
    ↓
FastAPI validation
    ↓
Telemetry and Vector3 objects
    ↓
Concurrent pair evaluation
    ↓
Closest-approach calculation
    ↓
Skip-list alert prioritization
    ↓
PostgreSQL/PostGIS persistence
    ↓
Prioritized alerts returned to React
```

The frontend is in `frontend/`. The Python API and algorithm implementation are
in `backend/`. PostgreSQL/PostGIS schema and indexes are in
`db/migrations/001_init.sql`.

## Collision calculation

The current model assumes that each object travels in a straight line at a
constant velocity during the prediction horizon. For each pair, the engine
computes:

1. Relative position: `position1 - position2`
2. Relative velocity: `velocity1 - velocity2`
3. Time of closest approach using the relative-motion dot-product formula
4. The predicted separation at that time
5. A conjunction alert when separation is at or below `threshold`

For `n` telemetry records, the current all-pairs calculation examines
`n * (n - 1) / 2` pairs, which is `O(n²)` time.

## Data structures

### `Vector3`

`Vector3` represents a three-dimensional position or velocity using `x`, `y`,
and `z` values. It provides vector subtraction and scaled addition so orbital
calculations remain explicit and type-safe.

### `Telemetry`

`Telemetry` is an immutable record containing an object ID, object type,
timestamp, position, and velocity. Incoming JSON records are converted into
these objects before detection begins.

### `ConjunctionAlert`

`ConjunctionAlert` stores the result of a pair calculation:

- Object IDs
- TCA
- Seconds until TCA
- Minimum separation
- Risk level
- Creation time
- Alert status

### Open-addressed hash set

`OpenAddressedHashSet` stores object IDs in an array using hashing and linear
probing. When a collision occurs, the next available slot is searched. The
table resizes when it reaches half capacity.

Average performance:

| Operation | Average complexity |
|---|---:|
| Insert | `O(1)` |
| Contains/search | `O(1)` |
| Resize | `O(n)` |

This custom structure provides fast satellite/debris ID indexing and duplicate
detection without relying on Python's built-in `set`.

### Randomized skip-list priority queue

`SkipListPriorityQueue` stores alerts by `time_to_tca_seconds`. The alert with
the smallest time to impact is removed first, ensuring urgent warnings are
processed before later warnings.

Each skip-list node has multiple forward links. Random node levels allow the
queue to skip over many nodes during insertion.

Expected performance:

| Operation | Expected complexity |
|---|---:|
| Insert | `O(log n)` |
| Remove minimum | `O(1)` |
| Search | `O(log n)` |

The queue grows dynamically as alerts are added. Its default maximum height is
16 levels.

### Thread pool

Pair calculations are independent, so `ThreadPoolExecutor` schedules them
concurrently. This improves throughput for I/O-heavy or moderate workloads.
For very large CPU-bound workloads, multiprocessing, vectorized numerical
processing, or a compiled computation service would be more appropriate.

## Risk classification

Risk is based on `minimum_separation / threshold`:

| Ratio | Risk level |
|---:|---|
| `<= 0.25` | Critical |
| `<= 0.50` | High |
| `<= 1.00` | Medium |
| `> 1.00` | Low |

Only pairs within the configured threshold are returned as conjunction alerts.

## Database tables

PostgreSQL with PostGIS stores the following:

- `telemetry`: object IDs, types, timestamps, 3D positions, and velocities
- `conjunction_alerts`: TCA, separation, risk, status, and object pairs
- `manoeuvre_logs`: planned or executed manoeuvre records

The telemetry position is stored as a PostGIS `PointZ` geometry. Indexes on
object/time, position, TCA, and alert status support faster retrieval.

## Current limitations and future work

The prototype currently uses constant-velocity motion rather than SGP4 or
Keplerian orbital propagation. It does not yet model uncertainty, manoeuvre
recommendations, authentication, streaming telemetry, or production safety
controls. The next major performance improvement would be spatial
partitioning or a three-dimensional nearest-neighbour index to reduce the
number of pair comparisons.
