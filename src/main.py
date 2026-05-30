import asyncio
import logging
import signal
import sys
from types import FrameType

from src.core.client import WildberriesApiClient
from src.core.scheduler import PricePollingScheduler
from src.limiter.token_bucket import TokenBucketLimiter
from src.metrics.server import MetricsServerManager

# Base logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("PyInfraGuard.Main")


class ApplicationContainer:
    """Orchestrates runtime lifecycle and dependencies of the monitoring service."""

    def __init__(self) -> None:
        self.metrics_server = MetricsServerManager(host="0.0.0.0", port=8000)
        self.limiter = TokenBucketLimiter(capacity=3.0, refill_rate=1.0)

        # Target test configuration params
        self.api_client = WildberriesApiClient(
            base_url="https://discounts-prices-api.wildberries.ru",
            token="YOUR_MOCK_TOKEN_HERE",
            limiter=self.limiter,
        )

        # Monitor specific item numbers (mock list)
        self.scheduler = PricePollingScheduler(
            api_client=self.api_client,
            nm_ids=[123456, 789012],
            interval_seconds=30.0,
        )
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        """Launch all background process subsystems and await termination signal."""
        logger.info("Initializing PyInfraGuard core systems...")

        # Start Prometheus exporter HTTP engine
        self.metrics_server.start()

        # Start periodic data loop as a task to prevent blocking
        scheduler_task = asyncio.create_task(self.scheduler.start())

        logger.info("Service infrastructure fully deployed. Entering operational loop.")

        # Setup POSIX signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._stop_event.set)

        # Keep running until signal event triggers
        await self._stop_event.wait()
        
        # Shutdown sequence
        scheduler_task.cancel()
        await self._shutdown()

    async def _shutdown(self) -> None:
        """Execute structured cleanup sequences for active components."""
        logger.info("Initiating graceful shutdown sequence...")
        await self.scheduler.stop()
        logger.info("PyInfraGuard core systems deactivated successfully.")


def handle_unhandled_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: FrameType | None,
) -> None:
    """Global hook to log critical errors that escaped standard try-except blocks."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical(
        "Unhandled system exception encountered", exc_info=(exc_type, exc_value, exc_traceback)
    )


if __name__ == "__main__":
    # Redirect global uncaught exceptions to logger
    sys.excepthook = handle_unhandled_exception  # type: ignore[assignment]

    container = ApplicationContainer()
    try:
        asyncio.run(container.run())
    except Exception as fatal_err:
        logger.critical(f"Fatal application startup failure: {fatal_err!s}", exc_info=True)
        sys.exit(1)
