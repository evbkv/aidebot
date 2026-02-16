# ==================== main.py ====================
#!/usr/bin/env python3
"""AideBot main entry point.

Starts polling for Telegram and/or MAX messengers based on configuration.
Telegram runs in a daemon thread, MAX runs in the main thread with auto‑restart.
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
)
from src.telegram_handler import TelegramHandler
from src.max_handler import MaxHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler('bot.log', encoding='utf-8')]
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize and start the bot for enabled messengers."""
    if len(GIGACHAT_CREDENTIALS) < 20:
        print("GIGACHAT TOKEN IS NOT CONFIGURED")
        return

    handlers = []

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
        handlers.append(tg_handler)
        tg_thread = threading.Thread(target=tg_handler.run_polling, daemon=True)
        tg_thread.start()
        logger.info("Telegram polling thread started")

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
        # MAX polling runs in the main thread; auto‑restart on crash
        while True:
            try:
                logger.info("Starting MAX polling loop")
                max_handler.run_polling()
            except Exception as e:
                logger.exception("MAX polling crashed, restarting in 5 seconds...")
                time.sleep(5)

    # If no MAX handler is running, keep the main thread alive
    if not MAX_ENABLED:
        logger.info("Bot is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down by user request")


if __name__ == "__main__":
    main()