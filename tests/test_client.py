from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter


@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(
        base_url="https://test.api", token="fake", limiter=limiter
    )

    mock_session = AsyncMock()

    # Упрощенная логика контекстного менеджера
    def create_mock_resp(status: int, json_data: dict[str, Any]) -> AsyncMock:
        mock_resp = AsyncMock()
        mock_resp.status = status
        mock_resp.json.return_value = json_data
        mock_resp.__aenter__.return_value = mock_resp
        return mock_resp

    mock_resp_429 = create_mock_resp(429, {})
    mock_resp_200 = create_mock_resp(200, {"data": {"products": []}})

    mock_session.get.side_effect = [mock_resp_429, mock_resp_200]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await client.fetch_prices(mock_session, [123])

    assert mock_session.get.call_count == 2
