from unittest.mock import AsyncMock, patch
import pytest
from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter

@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient("https://test.api", "fake", limiter)
    
    mock_session = AsyncMock()
    
    # Прямое определение ответа как контекстного менеджера
    resp = AsyncMock()
    resp.__aenter__.return_value = resp
    resp.json.side_effect = [{}, {"data": {"products": []}}]
    resp.status = 429
    # Хитрость: меняем статус после первого вызова
    resp.status = 429
    
    # Чтобы статус менялся:
    resp_429 = AsyncMock()
    resp_429.status = 429
    resp_429.__aenter__.return_value = resp_429
    resp_429.json.return_value = {}

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.__aenter__.return_value = resp_200
    resp_200.json.return_value = {"data": {"products": []}}

    mock_session.get.side_effect = [resp_429, resp_200]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await client.fetch_prices(mock_session, [123])

    assert mock_session.get.call_count == 2
