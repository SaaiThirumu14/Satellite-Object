from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar

T = TypeVar("T")


class OpenAddressedHashSet:
    """Linear-probing set used to index object IDs without dict lookups."""

    def __init__(self, capacity: int = 16) -> None:
        if capacity < 4:
            raise ValueError("capacity must be at least 4")
        self._slots: list[str | None] = [None] * capacity
        self._size = 0

    def add(self, value: str) -> None:
        if self._size * 2 >= len(self._slots):
            self._resize()
        index = hash(value) % len(self._slots)
        while self._slots[index] is not None:
            if self._slots[index] == value:
                return
            index = (index + 1) % len(self._slots)
        self._slots[index] = value
        self._size += 1

    def __contains__(self, value: str) -> bool:
        index = hash(value) % len(self._slots)
        for _ in self._slots:
            current = self._slots[index]
            if current is None:
                return False
            if current == value:
                return True
            index = (index + 1) % len(self._slots)
        return False

    def __len__(self) -> int:
        return self._size

    def _resize(self) -> None:
        values = [value for value in self._slots if value is not None]
        self._slots = [None] * (len(self._slots) * 2)
        self._size = 0
        for value in values:
            self.add(value)


@dataclass
class _Node(Generic[T]):
    key: float
    value: T
    forward: list["_Node[T] | None"]


class SkipListPriorityQueue(Generic[T]):
    def __init__(self, max_level: int = 16, seed: int | None = None) -> None:
        if max_level < 1:
            raise ValueError("max_level must be positive")
        self._max_level = max_level
        self._random = random.Random(seed)
        self._head = _Node(float("-inf"), None, [None] * max_level)  # type: ignore[arg-type]
        self._level = 1
        self._size = 0

    def push(self, key: float, value: T) -> None:
        update = [self._head] * self._max_level
        current = self._head
        for level in range(self._level - 1, -1, -1):
            while current.forward[level] is not None and current.forward[level].key <= key:
                current = current.forward[level]  # type: ignore[assignment]
            update[level] = current
        node_level = self._random_level()
        if node_level > self._level:
            update[self._level:node_level] = [self._head] * (node_level - self._level)
            self._level = node_level
        node = _Node(key, value, [None] * node_level)
        for level in range(node_level):
            node.forward[level] = update[level].forward[level]
            update[level].forward[level] = node
        self._size += 1

    def pop(self) -> T:
        node = self._head.forward[0]
        if node is None:
            raise IndexError("pop from empty priority queue")
        self._head.forward[0] = node.forward[0]
        self._size -= 1
        return node.value

    def __len__(self) -> int:
        return self._size

    def _random_level(self) -> int:
        level = 1
        while level < self._max_level and self._random.random() < 0.5:
            level += 1
        return level

