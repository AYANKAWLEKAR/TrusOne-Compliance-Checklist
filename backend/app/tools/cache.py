from __future__ import annotations

import time
from collections.abc import Callable


class TTLCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, object]] = {}

    def get_or_set(self, key: str, producer: Callable[[], object]) -> object:
        now = time.time()
        cached = self._store.get(key)
        if cached and cached[0] > now:
            return cached[1]
        value = producer()
        self._store[key] = (now + self.ttl_seconds, value)
        return value
