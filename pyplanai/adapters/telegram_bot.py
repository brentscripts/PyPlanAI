from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from pyplanai.core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from pyplanai.core.planner import PyPlanCore


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

    async def send(self, text: str) -> None:
        """Send a message to the configured Telegram chat."""
        from telegram import Bot
        bot = Bot(token=self.token)
        await bot.send_message(chat_id=self.chat_id, text=text)


def build_command_bot(core: PyPlanCore, token: str) -> Application:
    async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Usage: /skip <block_id>")
            return
        block = core.skip_block(int(context.args[0]))
        if block:
            await update.message.reply_text(
                f"Skipped block #{block.id}. That's just a red light, man. Next green light's coming."
            )
        else:
            await update.message.reply_text("Couldn't find that block, brother.")

    async def later(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Usage: /later <block_id> [minutes]")
            return
        block_id = int(context.args[0])
        if len(context.args) > 1:
            minutes = int(context.args[1])
        else:
            minutes = 30
        block = core.push_block_later(block_id, minutes)
        if block:
            await update.message.reply_text(
                f"Pushed block #{block.id} to {block.start_time}-{block.end_time}. We recalibrate, we roll."
            )
        else:
            await update.message.reply_text("Couldn't find that block, brother.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(CommandHandler("later", later))
    return app
