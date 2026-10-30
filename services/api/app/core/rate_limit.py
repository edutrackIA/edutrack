"""In-memory sliding-window limiter for failed attempts (login, invitation links).

It lives in the API process, which is enough for a single instance. With several
instances behind a load balancer the counters would have to move to Redis (ADR-0012).
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self, *, limit: int, window_seconds: int, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.limit = limit
        self.window = window_seconds
        self.clock = clock
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def retry_after(self, key: str) -> int | None:
        """Seconds to wait if the key is blocked; None if it may try again."""
        with self._lock:
            failures = self._recent(key)
            if len(failures) < self.limit:
                return None
            return max(1, math.ceil(failures[0] + self.window - self.clock()))

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._recent(key).append(self.clock())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()

    def _recent(self, key: str) -> deque[float]:
        failures = self._failures.setdefault(key, deque())
        cutoff = self.clock() - self.window
        while failures and failures[0] <= cutoff:
            failures.popleft()
        return failures


# Per account and address: slows down guessing one person's password.
login_by_account = RateLimiter(limit=5, window_seconds=15 * 60)
# Per address: slows down trying many accounts from the same place.
login_by_address = RateLimiter(limit=30, window_seconds=15 * 60)
# Per address: failed invitation lookups or acceptances.
invitations_by_address = RateLimiter(limit=20, window_seconds=15 * 60)

ALL_LIMITERS = (login_by_account, login_by_address, invitations_by_address)
