import pytest
from unittest.mock import AsyncMock, patch
from typing import Any

from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter


@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(
        base_url="https://test.api", token="fake", limiter=limiter
    )

    mock_session = AsyncMock()

    async def mock_context_manager(
        status: int, json_data: dict[str, Any] | None = None
    ) -> AsyncMock:
        mock_resp = AsyncMock()
        mock_resp.status = status
        mock_resp.json = AsyncMock(return_value=json_data or {})
        mock_resp.__aenter__.return_value = mock_resp
        return mock_resp

    mock_resp_429 = await mock_context_manager(429)
    mock_resp_200 = await mock_context_manager(200, {"data": {"products": []}})

    mock_session.get.side_effect = [mock_resp_429, mock_resp_200]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await client.fetch_prices(mock_session, [123])

    assert mock_session.get.call_count == 2
