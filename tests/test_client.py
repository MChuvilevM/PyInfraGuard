from unittest.mock import AsyncMock, patch

import pytest

from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter


@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(base_url="https://test.api", token="fake", limiter=limiter)

    mock_session = AsyncMock()

    # Настраиваем поведение контекстного менеджера
    async def mock_response_with_status(status: int, json_data: dict | None = None):
        resp = AsyncMock()
        resp.status = status
        resp.json = AsyncMock(return_value=json_data or {})
        # Это ключевая строка: заставляет работать async with
        resp.__aenter__.return_value = resp
        return resp

    mock_resp_429 = await mock_response_with_status(429)
    mock_resp_200 = await mock_response_with_status(200, {"data": {"products": []}})

    mock_session.get.side_effect = [mock_resp_429, mock_resp_200]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await client.fetch_prices(mock_session, [123])

    assert result is not None
    assert mock_session.get.call_count == 2
