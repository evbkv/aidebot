# ==================== src/storage.py ====================
"""Persist chat logs to disk and notify owner about new users."""

import os
import logging
from datetime import datetime
from . import notifier, utils

logger = logging.getLogger(__name__)


def log_message(messenger: str, user_id: int, sender: str, text: str, user_name: str = None, phone: str = None) -> bool:
    """Write a message to the user's chat log file. Return True on success."""
    try:
        if not utils.validate_messenger(messenger):
            logger.error(f"Invalid messenger: {messenger}")
            return False
        if not utils.validate_user_id(user_id):
            logger.error(f"Invalid user_id: {user_id}")
            return False

        safe_user_id = str(int(user_id))  # normalize
        path = f"chats/{messenger}/{safe_user_id}.txt"
        os.makedirs(os.path.dirname(path), exist_ok=True)

        first = not os.path.exists(path)

        # Format log entry with user name and phone if available
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if sender == 'user':
            if user_name and phone:
                log_entry = f"[{timestamp}] {sender} ({user_name}, {phone}): {text}\n"
            elif user_name:
                log_entry = f"[{timestamp}] {sender} ({user_name}): {text}\n"
            elif phone:
                log_entry = f"[{timestamp}] {sender} (phone: {phone}): {text}\n"
            else:
                log_entry = f"[{timestamp}] {sender}: {text}\n"
        else:
            log_entry = f"[{timestamp}] {sender}: {text}\n"

        with open(path, "a", encoding="utf-8") as f:
            f.write(log_entry)

        if first and sender == "user":
            notifier.notify_all_platforms(user_id, user_name or "Unknown", messenger, phone)

        return True
    except Exception as e:
        logger.exception(f"Failed to log message: {e}")
        return False