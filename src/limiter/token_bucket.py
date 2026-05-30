import asyncio
import time

from src.metrics.exporter import MetricsManager


class TokenBucketLimiter:
    """Thread-safe async Token Bucket rate limiter with Prometheus metrics integration."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        """Initialize the rate limiter.

        Args:
            capacity: Maximum number of tokens the bucket can hold.
            refill_rate: Number of tokens added to the bucket per second.
        """
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

        # Initial metric export
        MetricsManager.update_limiter_tokens(self._tokens)

    def _refill(self) -> None:
        """Refill the bucket with tokens based on elapsed time.

        Must be called under lock.
        """
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now

        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
            MetricsManager.update_limiter_tokens(self._tokens)

    async def acquire(self, tokens: float = 1.0) -> None:
        """Acquire the specified number of tokens. Blocks until tokens are available."""
        if tokens > self._capacity:
            MetricsManager.track_error(component="limiter")
            raise ValueError(f"Requested tokens ({tokens}) exceed bucket capacity ({self._capacity})")

        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    MetricsManager.update_limiter_tokens(self._tokens)
                    return

                # Calculate wait time based on missing tokens
                needed_tokens = tokens - self._tokens
                wait_time = needed_tokens / self._refill_rate

            # Ожидаем вне контекстного менеджера, чтобы не блокировать другие потоки
            await asyncio.sleep(wait_time)
