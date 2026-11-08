from __future__ import annotations

import os
from collections.abc import Sequence

from .algorithms import ConjunctionAlert, Telemetry


class DatabaseUnavailable(RuntimeError):
    pass


class ConjunctionRepository:
    def __init__(self) -> None:
        self._url = os.getenv("DATABASE_URL", "postgresql://conjunctions:conjunctions@localhost:5432/conjunctions")

    def save_detection(self, telemetry: Sequence[Telemetry], alerts: Sequence[ConjunctionAlert]) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise DatabaseUnavailable("database driver is not installed") from exc
        try:
            with psycopg.connect(self._url) as connection:
                with connection.cursor() as cursor:
                    for item in telemetry:
                        cursor.execute(
                            """INSERT INTO telemetry
                            (object_id, object_type, observed_at, position, velocity_x, velocity_y, velocity_z)
                            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s, %s), 4978), %s, %s, %s)""",
                            (item.object_id, item.object_type, item.timestamp, item.position.x,
                             item.position.y, item.position.z, item.velocity.x, item.velocity.y, item.velocity.z),
                        )
                    for alert in alerts:
                        cursor.execute(
                            """INSERT INTO conjunction_alerts
                            (object_1_id, object_2_id, tca, time_to_tca_seconds, minimum_separation,
                             risk_level, status, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                            (alert.object1_id, alert.object2_id, alert.tca, alert.time_to_tca_seconds,
                             alert.minimum_separation, alert.risk_level, alert.status, alert.created_at),
                        )
        except Exception as exc:
            raise DatabaseUnavailable("database unavailable") from exc

    def list_alerts(self, limit: int = 100) -> list[dict]:
        try:
            import psycopg
        except ImportError as exc:
            raise DatabaseUnavailable("database driver is not installed") from exc
        try:
            with psycopg.connect(self._url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT object_1_id, object_2_id, tca, time_to_tca_seconds,
                        minimum_separation, risk_level, created_at, status
                        FROM conjunction_alerts ORDER BY tca ASC LIMIT %s""",
                        (limit,),
                    )
                    columns = [column.name for column in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as exc:
            raise DatabaseUnavailable("database unavailable") from exc

