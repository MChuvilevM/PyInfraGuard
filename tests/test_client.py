@pytest.mark.asyncio
async def test_fetch_prices_retry_on_429() -> None:
    limiter = TokenBucketLimiter(capacity=10, refill_rate=1)
    client = WildberriesApiClient(
        base_url="https://test.api", token="fake", limiter=limiter
    )

    mock_session = AsyncMock()

    # Создаем объект-ответ, который гарантированно является контекстным менеджером
    def create_mock_resp(status: int, json_data: dict[str, Any]) -> AsyncMock:
        mock_resp = AsyncMock()
        mock_resp.status = status
        mock_resp.json = AsyncMock(return_value=json_data)
        
        # Определяем поведение контекстного менеджера
        manager = AsyncMock()
        manager.__aenter__.return_value = mock_resp
        return manager

    # Передаем этот менеджер как результат вызова .get()
    mock_session.get.side_effect = [
        create_mock_resp(429, {}),
        create_mock_resp(200, {"data": {"products": []}})
    ]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await client.fetch_prices(mock_session, [123])

    assert mock_session.get.call_count == 2
