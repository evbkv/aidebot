# ==================== src/utils.py ====================
"""Utility functions: text cleaning, validation, rate limiting, message splitting."""

import re
import time
from collections import deque

# In‑memory rate limit storage
_user_requests = {}


def clean_text(text: str) -> str:
    """Remove HTML tags and Markdown formatting characters."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\*\*|__|\*|_|~~|\+\+|`", "", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def validate_user_id(uid) -> bool:
    """Return True if uid consists only of digits."""
    return str(uid).isdigit()


def validate_messenger(messenger: str) -> bool:
    """Return True if messenger name is allowed."""
    return messenger in ("telegram", "max")


def is_rate_limited(user_id: int, limit: int = 10, period: int = 60) -> bool:
    """Check if the user has exceeded the rate limit."""
    now = time.time()
    if user_id not in _user_requests:
        _user_requests[user_id] = deque()
    dq = _user_requests[user_id]
    # remove old timestamps
    while dq and dq[0] < now - period:
        dq.popleft()
    if len(dq) >= limit:
        return True
    dq.append(now)
    return False


def send_long_message(chat_id: int, text: str, split_needed: bool, send_func, platform: str = None) -> None:
    """
    Send a long message, splitting into 4000‑character chunks if needed.
    Works for both sync and async send_func (async will be scheduled).
    """
    if not split_needed:
        send_func(chat_id, text)
        return
    parts = [text[i:i + 4000] for i in range(0, len(text), 4000)]
    for i, part in enumerate(parts, 1):
        send_func(chat_id, f"({i}/{len(parts)})\n{part}")