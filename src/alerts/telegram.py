import logging

from aiogram import Bot


logger = logging.getLogger(__name__)


class TelegramAlertManager:
    def __init__(self, token: str, chat_id: str) -> None:
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def send_alert(self, message: str) -> None:
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send telegram alert: {e}")

    async def close(self) -> None:
        await self.bot.session.close()
