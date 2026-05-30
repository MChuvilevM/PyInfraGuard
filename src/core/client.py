import asyncio
import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from src.core.schemas import WBApiResponse
from src.limiter.token_bucket import TokenBucketLimiter
from src.metrics.exporter import MetricsManager

logger = logging.getLogger("PyInfraGuard.CoreClient")


class WildberriesApiClient:
    """Asynchronous robust HTTP client for Wildberries API integration with metrics."""

    def __init__(self, base_url: str, token: str, limiter: TokenBucketLimiter) -> None:
        """Initialize the API client with required credentials and rate limiter."""
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._limiter = limiter
        self._timeout = ClientTimeout(total=15.0, connect=5.0)

    async def fetch_prices(self, session: ClientSession, nm_ids: list[int]) -> WBApiResponse:
        """Fetch product price data by marketplace article IDs with retry logic."""
        url = f"{self._base_url}/api/v1/prices"
        params = {"nmIds": ",".join(map(str, nm_ids))}

        await self._limiter.acquire(tokens=1)

        for attempt in range(3):
            with MetricsManager.measure_latency(method="fetch_prices"):
                try:
                    async with session.get(
                        url, headers=self._headers, params=params, timeout=self._timeout
                    ) as response:
                        MetricsManager.track_request(method="fetch_prices", status_code=response.status)

                        if response.status == 429:
                            wait = 2**attempt
                            logger.warning("Rate limit hit. Retry %d/3 in %ds", attempt + 1, wait)
                            await asyncio.sleep(wait)
                            continue

                        response.raise_for_status()
                        response_json = await response.json()
                        return WBApiResponse.model_validate(response_json)

                except Exception as err:
                    if attempt == 2:
                        logger.error("Final failure after 3 attempts: %s", err, exc_info=True)
                        MetricsManager.track_error(component="api_client_exception")
                        raise
                    await asyncio.sleep(1)

        raise RuntimeError("Unreachable code in fetch_prices")
