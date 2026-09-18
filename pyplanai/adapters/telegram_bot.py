from __future__ import annotations

from pyplanai.core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

    async def send(self, text: str) -> None:
        """Send a message to the specified Telegram chat."""
        from telegram import Bot
        bot = Bot(token=self.token)
        await bot.send_message(chat_id=self.chat_id, text=text)
