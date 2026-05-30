import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from src.core.schemas import WBApiResponse
from src.limiter.token_bucket import TokenBucketLimiter


logger = logging.getLogger("PyInfraGuard.CoreClient")


class WildberriesApiClient:
    """Асинхронный отказоустойчивый клиент для работы с API Wildberries."""

    def __init__(self, base_url: str, token: str, limiter: TokenBucketLimiter) -> None:
        """Инициализация клиента.

        Args:
            base_url: Базовый URL API маркетплейса.
            token: Авторизационный токен (API-ключ).
            limiter: Экземпляр TokenBucketLimiter для контроля частоты запросов.
        """
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._limiter = limiter
        self._timeout = ClientTimeout(total=15.0, connect=5.0)

    async def fetch_prices(self, session: ClientSession, nm_ids: list[int]) -> WBApiResponse:
        """Запрашивает данные о ценах товаров по их артикулам (nmId).

        Метод гарантированно ожидает разрешения от Rate Limiter перед отправкой.

        Args:
            session: Текущая сессия aiohttp.
            nm_ids: Список артикулов для проверки.

        Returns:
            Валидированный объект WBApiResponse.
        """
        url = f"{self._base_url}/api/v1/prices"
        params = {"nmIds": ",".join(map(str, nm_ids))}

        # Жесткое ограничение частоты перед сетевым вызовом
        await self._limiter.acquire(tokens=1)

        try:
            async with session.get(url, headers=self._headers, params=params, timeout=self._timeout) as response:
                if response.status == 429:
                    logger.error("Критическая ошибка: Превышен лимит запросов (HTTP 429), несмотря на лимитер.")
                    response.raise_for_status()

                response.raise_for_status()
                response_json = await response.json()

                # Жесткая валидация схемы данных через Pydantic
                return WBApiResponse.model_validate(response_json)

        except Exception as err:
            logger.error(f"Ошибка при выполнении запроса к WB API: {err!s}", exc_info=True)
            raise
