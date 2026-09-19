from __future__ import annotations

import asyncio
import logging

from pyplanai.core.planner import PyPlanCore
from pyplanai.adapters.notify_desktop import send_desktop_notification
from pyplanai.adapters.telegram_bot import TelegramNotifier, build_command_bot
from pyplanai.core.config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pyplanai.daemon")

POLL_INTERVAL_SECONDS = 30
LOOKAHEAD_MINUTES = 2


async def scheduler_loop(core: PyPlanCore, telegram: TelegramNotifier) -> None:
    while True:
        try:
            due_blocks = core.get_upcoming_blocks_needing_notification(LOOKAHEAD_MINUTES)
            for block in due_blocks:
                message = f"Ding! Two-Minute Warning — Up next: {block.action_cue}. /skip {block.id} or /later {block.id}"
                send_desktop_notification("PyPlanAI", message)
                await telegram.send(message)
                core.db.mark_notified(block.id)
                logger.info("Notified for block #%s", block.id)
        except Exception:
            logger.exception("Error in scheduler loop")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def main() -> None:
    core = PyPlanCore()
    telegram = TelegramNotifier()
    command_bot = build_command_bot(core, TELEGRAM_BOT_TOKEN)

    await command_bot.initialize()
    await command_bot.start()
    await command_bot.updater.start_polling()

    await scheduler_loop(core, telegram)


if __name__ == "__main__":
    asyncio.run(main())