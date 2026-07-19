"""Small, replaceable security primitives for the single-process MVP."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class _Window:
    started_at: float
    count: int


class InMemoryFixedWindowRateLimiter:
    """Thread-safe fixed-window limiter. Replace with Redis when API replicas are added."""

    def __init__(self, requests: int, window_seconds: int) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self._windows: dict[str, _Window] = {}
        self._lock = threading.Lock()

    def check(self, key: str, *, now: float | None = None) -> tuple[bool, int]:
        current = time.monotonic() if now is None else now
        with self._lock:
            window = self._windows.get(key)
            if window is None or current - window.started_at >= self.window_seconds:
                self._windows[key] = _Window(started_at=current, count=1)
                return True, 0
            if window.count >= self.requests:
                retry_after = max(1, int(self.window_seconds - (current - window.started_at)) + 1)
                return False, retry_after
            window.count += 1
            return True, 0
