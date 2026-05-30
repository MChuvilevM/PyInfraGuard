import asyncio
import logging

from aiohttp import ClientSession

from src.core.client import WildberriesApiClient
from src.metrics.exporter import MetricsManager


logger = logging.getLogger("PyInfraGuard.Scheduler")


class PricePollingScheduler:
    """Periodic task scheduler for fetching marketplace data with structured monitoring."""

    def __init__(
        self,
        api_client: WildberriesApiClient,
        nm_ids: list[int],
        interval_seconds: float = 60.0,
    ) -> None:
        """Initialize the polling scheduler.

        Args:
            api_client: Integrated Wildberries API client.
            nm_ids: Target marketplace product identifiers.
            interval_seconds: Execution cycle delay in seconds.
        """
        self._api_client = api_client
        self._nm_ids = nm_ids
        self._interval = interval_seconds
        self._is_running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the background periodic polling loop."""
        if self._is_running:
            logger.warning("Scheduler loop is already active.")
            return

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Price polling scheduler activated with interval: {self._interval}s")

    async def stop(self) -> None:
        """Gracefully stop the background polling loop and await pending operations."""
        if not self._is_running:
            return

        self._is_running = False
        logger.info("Deactivating price polling scheduler...")

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.debug("Scheduler background task successfully cancelled.")
            finally:
                self._task = None

        logger.info("Price polling scheduler stopped.")

    async def _run_loop(self) -> None:
        """Internal infinite execution loop handled via aiohttp session architecture."""
        async with ClientSession() as session:
            while self._is_running:
                start_time = asyncio.get_running_loop().time()
                logger.debug("Starting periodic price sync execution cycle.")

                try:
                    response = await self._api_client.fetch_prices(session, self._nm_ids)
                    logger.info(f"Successfully synchronized data for {len(response.data.list)} items.")
                except Exception as err:
                    logger.error(f"Execution cycle execution failure: {err!s}", exc_info=True)
                    MetricsManager.track_error(component="scheduler_cycle")

                # Precision interval alignment calculation
                elapsed = asyncio.get_running_loop().time() - start_time
                sleep_time = max(0.0, self._interval - elapsed)

                try:
                    await asyncio.sleep(sleep_time)
                except asyncio.CancelledError:
                    break
