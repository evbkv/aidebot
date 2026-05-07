# ==================== main.py ====================
#!/usr/bin/env python3
"""AideBot main entry point.

Starts polling for Telegram and/or MAX messengers based on configuration.
Telegram runs in the main thread, MAX and WEB run in daemon threads.
"""

import logging
import threading
import time
from config import (
    TELEGRAM_ENABLED,
    MAX_ENABLED,
    GIGACHAT_CREDENTIALS,
    TELEGRAM_BOT_TOKEN,
    MAX_BOT_TOKEN,
    TELEGRAM_ALLOWED_USER_ID,
    MAX_ALLOWED_USER_ID,
    TELEGRAM_SUPERUSER_ENABLED,
    MAX_SUPERUSER_ENABLED,
    MAX_API_BASE,
    WEB_ENABLED,
    WEB_HOST,
    WEB_PORT,
    WEB_ALLOWED_ORIGINS,
    LOG_TO_FILE,
)
from src.telegram_handler import TelegramHandler
from src.max_handler import MaxHandler
from src.web_handler import WebHandler

handlers = [logging.StreamHandler()]
if LOG_TO_FILE:
    handlers.append(logging.FileHandler('bot.log', encoding='utf-8'))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=handlers
)
logger = logging.getLogger(__name__)


def run_max_polling(handler):
    """Run MAX polling with auto‑restart in a separate thread."""
    while True:
        try:
            logger.info("Starting MAX polling loop")
            handler.run_polling()
        except Exception as e:
            logger.exception("MAX polling crashed, restarting in 5 seconds...")
            time.sleep(5)


def main() -> None:
    """Initialize and start the bot for enabled messengers."""
    if len(GIGACHAT_CREDENTIALS) < 20:
        print("GIGACHAT TOKEN IS NOT CONFIGURED")
        return

    if WEB_ENABLED:
        web_handler = WebHandler(
            platform="web",
            owner_id=0,
            superuser_enabled=False,
            host=WEB_HOST,
            port=WEB_PORT,
            allowed_origins=WEB_ALLOWED_ORIGINS
        )
        web_thread = threading.Thread(target=web_handler.run_polling, daemon=True)
        web_thread.start()
        logger.info("Web widget thread started")

    if MAX_ENABLED:
        if not MAX_BOT_TOKEN or len(MAX_BOT_TOKEN) < 10:
            print("ERROR: MAX token not specified")
            return
        max_handler = MaxHandler(
            platform="max",
            owner_id=MAX_ALLOWED_USER_ID,
            superuser_enabled=MAX_SUPERUSER_ENABLED,
            token=MAX_BOT_TOKEN,
            api_base=MAX_API_BASE,
        )
        max_thread = threading.Thread(target=run_max_polling, args=(max_handler,), daemon=True)
        max_thread.start()
        logger.info("MAX polling thread started")

    if TELEGRAM_ENABLED:
        if not TELEGRAM_BOT_TOKEN or len(TELEGRAM_BOT_TOKEN) < 10:
            print("ERROR: Telegram token not specified")
            return
        tg_handler = TelegramHandler(
            platform="telegram",
            owner_id=TELEGRAM_ALLOWED_USER_ID,
            superuser_enabled=TELEGRAM_SUPERUSER_ENABLED,
            token=TELEGRAM_BOT_TOKEN,
        )
        logger.info("Starting Telegram polling in main thread")
        tg_handler.run_polling()
    else:
        logger.info("Bot is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down by user request")


if __name__ == "__main__":
    main()