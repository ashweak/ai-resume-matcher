"""Simple in-memory limiter so one visitor can't use up the free AI quota."""
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_calls: int, per_seconds: int = 3600):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self.calls: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        if self.max_calls <= 0:  # 0 = unlimited
            return True
        now = time.monotonic()
        with self.lock:
            q = self.calls[key]
            while q and now - q[0] > self.per_seconds:
                q.popleft()
            if len(q) >= self.max_calls:
                return False
            q.append(now)
            return True
