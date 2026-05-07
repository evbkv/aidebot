# ==================== src/notifier.py ====================
"""Notify the owner about new users on all enabled platforms."""

import requests
import logging
import html
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_ID, MAX_ALLOWED_USER_ID, MAX_API_BASE

logger = logging.getLogger(__name__)

_max_headers = None


def set_max_headers(headers: dict) -> None:
    """Store headers for MAX API calls (used by notifier)."""
    global _max_headers
    _max_headers = headers


def _send_notification(platform: str, user_id: int, user_name: str, source: str, phone: str = None) -> None:
    """Send a notification message to the owner on the given platform."""
    # Build common notification text
    base_text = f"New user {source}: {user_name} (ID: {user_id})"
    if phone:
        base_text += f", phone: {phone}"
    summary_cmd = f"\n/summary {source} {user_id}"
    text = base_text + summary_cmd

    if platform == 'telegram':
        safe_name = html.escape(user_name)
        # Create a clickable link to the user (opens chat with user)
        user_link = f'<a href="tg://user?id={user_id}">{safe_name}</a>'
        # Rebuild text with link for Telegram
        linked_base = f"New user {source}: {user_link} (ID: {user_id})"
        if phone:
            linked_base += f", phone: {phone}"
        text = linked_base + summary_cmd

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_ALLOWED_USER_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            requests.post(url, json=data, timeout=10)
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")

    elif platform == 'max':
        if not _max_headers:
            return
        url = f"{MAX_API_BASE}/messages?chat_id={MAX_ALLOWED_USER_ID}"
        data = {"text": text}
        try:
            requests.post(url, headers=_max_headers, json=data, timeout=10)
        except Exception as e:
            logger.error(f"MAX notification failed: {e}")


def notify_all_platforms(user_id: int, user_name: str, source: str, phone: str = None) -> None:
    """Send new‑user notification to the owner on all enabled platforms."""
    from config import TELEGRAM_SUPERUSER_ENABLED, MAX_SUPERUSER_ENABLED
    if TELEGRAM_SUPERUSER_ENABLED and user_id != TELEGRAM_ALLOWED_USER_ID:
        _send_notification('telegram', user_id, user_name, source, phone)
    if MAX_SUPERUSER_ENABLED and user_id != MAX_ALLOWED_USER_ID:
        _send_notification('max', user_id, user_name, source, phone)