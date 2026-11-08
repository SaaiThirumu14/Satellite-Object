from datetime import datetime, timezone

from app.algorithms import Telemetry, Vector3, detect_conjunctions
from app.data_structures import OpenAddressedHashSet, SkipListPriorityQueue

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_closest_pair_is_critical_and_sorted():
    alerts = detect_conjunctions([
        Telemetry("A", "satellite", START, Vector3(0, 0, 0), Vector3(1, 0, 0)),
        Telemetry("B", "debris", START, Vector3(5, 0, 0), Vector3(-1, 0, 0)),
    ], 2, 10, START)
    assert len(alerts) == 1
    assert alerts[0].minimum_separation == 0
    assert alerts[0].risk_level == "critical"


def test_custom_structures_handle_duplicates_and_priority():
    values = OpenAddressedHashSet(4)
    for value in ("a", "b", "c", "a"):
        values.add(value)
    assert len(values) == 3
    assert "missing" not in values

    queue = SkipListPriorityQueue[str](seed=1)
    queue.push(3, "late")
    queue.push(1, "early")
    queue.push(2, "middle")
    assert [queue.pop(), queue.pop(), queue.pop()] == ["early", "middle", "late"]
