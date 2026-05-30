import pytest
from unittest.mock import AsyncMock, patch
from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter

@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    # 1. Настройка
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(base_url="https://test.api", token="fake", limiter=limiter)
    
    mock_session = AsyncMock()
    # Имитируем: сначала 429 (ошибка), потом 200 (успех)
    mock_response = AsyncMock()
    mock_response.status = 429
    
    mock_success = AsyncMock()
    mock_success.status = 200
    mock_success.json.return_value = {"data": {"products": []}}
    
    mock_session.get.side_effect = [mock_response, mock_success]
    
    # 2. Выполнение
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await client.fetch_prices(mock_session, [123])
    
    # 3. Проверка
    assert result is not None
    assert mock_session.get.call_count == 2
