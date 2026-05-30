import pytest
from unittest.mock import AsyncMock, patch

from src.core.client import WildberriesApiClient
from src.limiter.token_bucket import TokenBucketLimiter


@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    # Настройка клиента
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(
        base_url="https://test.api", token="fake", limiter=limiter
    )

    # Создаем мок сессии
    mock_session = AsyncMock()

    # Настраиваем мок ответа для 429 и 200
    # Нам нужно, чтобы session.get(...) возвращал контекстный менеджер
    
    async def mock_context_manager(status, json_data=None):
        mock_resp = AsyncMock()
        mock_resp.status = status
        mock_resp.json = AsyncMock(return_value=json_data or {})
        # Это самое важное: имитируем поведение async with
        mock_resp.__aenter__.return_value = mock_resp
        return mock_resp

    mock_resp_429 = await mock_context_manager(429)
    mock_resp_200 = await mock_context_manager(200, {"data": {"products": []}})

    # Первый вызов вернет 429, второй — 200
    mock_session.get.side_effect = [mock_resp_429, mock_resp_200]

    # Запуск теста с подменой asyncio.sleep
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await client.fetch_prices(mock_session, [123])

    assert result is not None
    assert mock_session.get.call_count == 2
