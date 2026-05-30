from unittest.mock import AsyncMock, patch

import pytest

from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter


@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(base_url="https://test.api", token="fake", limiter=limiter)

    mock_session = AsyncMock()

    async def get_mock_resp(status: int) -> AsyncMock:
        m = AsyncMock()
        m.status = status
        m.json = AsyncMock(return_value={"data": {"products": []}})
        m.__aenter__.return_value = m
        return m

    mock_session.get.side_effect = [
        await get_mock_resp(429),
        await get_mock_resp(200),
    ]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await client.fetch_prices(mock_session, [123])

    assert mock_session.get.call_count == 2
