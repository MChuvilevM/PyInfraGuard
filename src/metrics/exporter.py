import time
from prometheus_client import Counter, Gauge, Histogram


# Метрики мониторинга производительности
WB_REQUESTS_TOTAL = Counter(
    "wb_requests_total",
    "Total number of requests sent to Wildberries API",
    ["method", "status_code"],
)

WB_REQUEST_LATENCY_SECONDS = Histogram(
    "wb_request_latency_seconds",
    "Latency of Wildberries API requests in seconds",
    ["method"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0),
)

WB_LIMITER_TOKENS = Gauge(
    "wb_limiter_tokens",
    "Current number of available tokens in the Rate Limiter bucket",
)

SYSTEM_ERRORS_TOTAL = Counter(
    "system_errors_total",
    "Total number of internal system errors logged",
    ["component"],
)


class MetricsManager:
    """Helper class to track and export core service metrics."""

    @staticmethod
    def track_request(method: str, status_code: int) -> None:
        """Increment the request counter with specific HTTP status."""
        WB_REQUESTS_TOTAL.labels(method=method, status_code=status_code).inc()

    @staticmethod
    def track_error(component: str) -> None:
        """Increment internal error counter for specific component."""
        SYSTEM_ERRORS_TOTAL.labels(component=component).inc()

    @staticmethod
    def update_limiter_tokens(tokens: float) -> None:
        """Update gauge showing current token bucket balance."""
        WB_LIMITER_TOKENS.set(tokens)

    @staticmethod
    def measure_latency(method: str) -> Histogram._UpperBoundedContextManager:
        """Context manager to measure execution latency of API calls."""
        return WB_REQUEST_LATENCY_SECONDS.labels(method=method).time()
