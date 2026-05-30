import logging

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
        """Fetch product price data by marketplace article IDs with precise metric tracking.

        This method acquires tokens from the rate limiter before executing the request.
        """
        url = f"{self._base_url}/api/v1/prices"
        params = {"nmIds": ",".join(map(str, nm_ids))}

        # Rate limiting block
        await self._limiter.acquire(tokens=1)

        # Measure request execution latency and track response codes
        with MetricsManager.measure_latency(method="fetch_prices"):
            try:
                async with session.get(url, headers=self._headers, params=params, timeout=self._timeout) as response:
                    MetricsManager.track_request(method="fetch_prices", status_code=response.status)

                    if response.status == 429:
                        logger.error("Critical error: Rate limit exceeded (HTTP 429) despite rate limiter.")
                        MetricsManager.track_error(component="api_client_429")
                        response.raise_for_status()

                    response.raise_for_status()
                    response_json = await response.json()

                    # Strict validation via Pydantic schema
                    return WBApiResponse.model_validate(response_json)

            except Exception as err:
                logger.error(f"Failed to fetch prices from WB API: {err!s}", exc_info=True)
                MetricsManager.track_error(component="api_client_exception")
                raise
