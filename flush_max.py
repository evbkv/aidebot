#!/usr/bin/env python3
"""
flush_max.py - скрипт для очистки очереди сообщений MAX.

Запустите этот скрипт, чтобы получить и залогировать все накопившиеся сообщения из MAX,
не отправляя на них ответы. После того как сообщения перестанут приходить,
можно запускать основной бот – он начнёт с чистого листа.
"""

import logging
import requests
import time
import json
import os
from config import MAX_BOT_TOKEN, MAX_API_BASE

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler('flush_max.log', encoding='utf-8')]
)
logger = logging.getLogger(__name__)

MARKER_FILE = "max_marker_flush.json"


def load_marker():
    try:
        if os.path.exists(MARKER_FILE):
            with open(MARKER_FILE, 'r') as f:
                data = json.load(f)
                return data.get('marker')
    except Exception as e:
        logger.error(f"Failed to load marker: {e}")
    return None


def save_marker(marker):
    try:
        with open(MARKER_FILE, 'w') as f:
            json.dump({'marker': marker}, f)
    except Exception as e:
        logger.error(f"Failed to save marker: {e}")


def main():
    if not MAX_BOT_TOKEN:
        logger.error("MAX_BOT_TOKEN not set in config.py")
        return

    headers = {"Authorization": MAX_BOT_TOKEN, "Content-Type": "application/json"}
    marker = load_marker()
    logger.info(f"Starting flush with marker: {marker}")
    error_delay = 1

    while True:
        try:
            params = {"marker": marker} if marker else {}
            resp = requests.get(
                f"{MAX_API_BASE}/updates",
                headers=headers,
                params=params,
                timeout=35,
            )

            if resp.status_code != 200:
                logger.warning(f"Updates status: {resp.status_code}")
                time.sleep(error_delay)
                error_delay = min(error_delay * 2, 30)
                continue

            error_delay = 1
            data = resp.json()
            updates = data.get("updates", []) if isinstance(data, dict) else []
            new_marker = data.get("marker") if isinstance(data, dict) else None

            for event in updates:
                if event.get("update_type") != "message_created":
                    continue

                msg = event.get("message", {})
                chat_id = msg.get("recipient", {}).get("chat_id")
                text = msg.get("body", {}).get("text")
                user_id = msg.get("sender", {}).get("user_id")
                user_name = msg.get("sender", {}).get("name", "Unknown")

                logger.info(f"FLUSH: user {user_id} ({user_name}) in chat {chat_id}: {text}")

            if new_marker and new_marker != marker:
                marker = new_marker
                save_marker(marker)
                logger.info(f"Marker updated to {marker}")

            if not updates:
                logger.info("No more updates. Waiting 10 seconds...")
                time.sleep(10)

        except requests.exceptions.Timeout:
            logger.warning("Timeout")
            time.sleep(error_delay)
        except Exception as e:
            logger.exception(f"Error: {e}")
            time.sleep(error_delay)


if __name__ == "__main__":
    main()