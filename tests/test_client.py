import pytest
from unittest.mock import patch, MagicMock

# Создаем простую заглушку, которая не является корутиной
class MockResponse:
    def __init__(self, status, json_data):
        self.status = status
        self.json_data = json_data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        pass
        
    async def json(self):
        return self.json_data

@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429(mocker) -> None:
    # ... тут инициализация клиента ...
    mock_session = MagicMock()
    # Возвращаем наш класс-заглушку, который гарантированно работает
    mock_session.get.side_effect = [
        MockResponse(429, {}),
        MockResponse(200, {"data": {"products": []}})
    ]
    # ... вызов и ассерты ...
