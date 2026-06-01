import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter

@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient("https://test.api", "fake", limiter)
    
    mock_session = MagicMock()

    # Создаем функцию-помощник для правильного мока контекстного менеджера
    def create_response(status, json_data):
        mock_resp = MagicMock()
        mock_resp.status = status
        mock_resp.json = AsyncMock(return_value=json_data)
        # Это то, что делает класс контекстным менеджером
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        return mock_resp

    mock_session.get.side_effect = [
        create_response(429, {}),
        create_response(200, {"data": {"products": []}})
    ]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await client.fetch_prices(mock_session, [123])

    assert mock_session.get.call_count == 2
