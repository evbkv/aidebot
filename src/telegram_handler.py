# ==================== src/telegram_handler.py ====================
"""Telegram bot polling and message handling using python-telegram-bot."""

import logging
import os
import sys
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_ID
from .base_handler import MessengerHandler
from .i18n import get_text

logger = logging.getLogger(__name__)


class TelegramHandler(MessengerHandler):
    """Handler for Telegram messenger."""

    def __init__(self, platform: str, owner_id: int, superuser_enabled: bool, token: str):
        super().__init__(platform, owner_id, superuser_enabled)
        self.token = token
        self.app = None

    def send_message(self, chat_id: int, text: str) -> None:
        """Send a message via Telegram (asynchronous, but called from sync context)."""
        import asyncio
        if self.app:
            asyncio.create_task(self.app.bot.send_message(chat_id=chat_id, text=text))

    def get_user_language(self, update: Update) -> str:
        """Extract language code from Telegram update."""
        return 'ru'   # Force Russian for consistency

    async def _handle_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Async handler that wraps the common process_message logic."""
        user = update.effective_user
        text = update.message.text
        chat_id = update.message.chat_id

        # owner restart command
        if text.startswith("/restart") and user.id == self.owner_id:
            await update.message.reply_text("Restarting the bot...")
            os.execl(sys.executable, sys.executable, *sys.argv)
            return

        self.process_message(
            user_id=user.id,
            chat_id=chat_id,
            text=text,
            user_name=user.full_name,
            update=update,
        )

    def run_polling(self) -> None:
        """Start Telegram bot polling with proper asyncio setup."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(MessageHandler(filters.TEXT, self._handle_async))
        logger.info("Telegram polling started")
        
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=1.0,
        )