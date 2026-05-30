import asyncio
import time


class TokenBucketLimiter:
    """Потокобезопасный асинхронный Rate Limiter на основе алгоритма Token Bucket."""

    def __init__(self, capacity: int, refill_rate: float) -> None:
        """Инициализация лимитера.

        Args:
            capacity: Максимальное количество токенов в корзине (максимальный всплеск запросов).
            refill_rate: Скорость восполнения токенов (количество токенов в секунду).
        """
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Внутренний метод для пересчета токенов на основе прошедшего времени."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(float(self._capacity), self._tokens + elapsed * self._refill_rate)
            self._last_refill = now

    async def acquire(self, tokens: int = 1) -> None:
        """Запрашивает указанное количество токенов.

        Если токенов недостаточно, приостанавливает выполнение (co-routine)
        до тех пор, пока корзина не накопит нужное количество.

        Args:
            tokens: Количество запрашиваемых токенов для операции.
        """
        if tokens > self._capacity:
            raise ValueError(f"Запрошено токенов ({tokens}) больше, чем максимальная емкость ({self._capacity})")

        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                # Вычисляем время ожидания до появления нужного количества токенов
                needed_tokens = tokens - self._tokens
                wait_time = needed_tokens / self._refill_rate
                await asyncio.sleep(wait_time)
