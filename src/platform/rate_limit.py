"""Configurable fixed-window request limiting with optional Redis coordination."""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class FixedWindowLimiter:
    """Use Redis across workers when configured and a local fallback otherwise."""

    def __init__(
        self,
        limit: int,
        redis_url: str | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.limit = limit
        self.clock = clock
        self._lock = threading.Lock()
        self._local_counts: dict[tuple[str, int], int] = {}
        self._redis = None
        if redis_url:
            try:
                import redis

                self._redis = redis.Redis.from_url(
                    redis_url, socket_timeout=0.5, socket_connect_timeout=0.5
                )
            except ImportError:
                logger.warning("redis_client_unavailable", extra={"error_type": "ImportError"})

    def allow(self, key: str) -> bool:
        bucket = int(self.clock() // 60)
        if self._redis is not None:
            try:
                count = self._redis.eval(
                    "local count = redis.call('INCR', KEYS[1]); "
                    "if count == 1 then redis.call('EXPIRE', KEYS[1], 60) end; "
                    "return count",
                    1,
                    f"support-agent:ratelimit:{bucket}:{key}",
                )
                return int(count) <= self.limit
            except Exception as exc:
                logger.warning(
                    "redis_rate_limit_fallback",
                    extra={"error_type": type(exc).__name__},
                )
        with self._lock:
            self._local_counts = {
                entry: count
                for entry, count in self._local_counts.items()
                if entry[1] >= bucket - 1
            }
            local_key = (key, bucket)
            count = self._local_counts.get(local_key, 0) + 1
            self._local_counts[local_key] = count
            return count <= self.limit
