import pytest
from unittest.mock import AsyncMock, patch
from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter

@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(base_url="https://test.api", token="fake", limiter=limiter)
    
    # 1. Создаем мок сессии
    mock_session = AsyncMock()
    
    # 2. Создаем мок ответа, который поддерживает async with
    mock_response = AsyncMock()
    mock_response.status = 429
    # Важно: настраиваем __aenter__, чтобы он возвращал сам мок
    mock_response.__aenter__.return_value = mock_response
    
    mock_success = AsyncMock()
    mock_success.status = 200
    mock_success.json = AsyncMock(return_value={"data": {"products": []}})
    mock_success.__aenter__.return_value = mock_success
    
    # 3. Назначаем side_effect (первый вызов - 429, второй - 200)
    mock_session.get.return_value = mock_response # Это нужно для корректной работы
    # Для side_effect с контекстными менеджерами лучше так:
    mock_session.get.side_effect = [mock_response, mock_success]
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await client.fetch_prices(mock_session, [123])
    
    assert result is not None
    assert mock_session.get.call_count == 2
