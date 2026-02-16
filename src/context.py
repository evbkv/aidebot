# ==================== src/context.py ====================
"""Manage conversation context (history) for each user per messenger."""

from collections import deque
import os

_history = {}


def _load_history_from_disk(messenger: str, user_id: int, maxlen: int = 5) -> deque:
    """Load the last `maxlen` lines from the user's chat log file."""
    path = f"chats/{messenger}/{user_id}.txt"
    if not os.path.exists(path):
        return deque(maxlen=maxlen)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # take last maxlen lines without parsing
    history = deque(maxlen=maxlen)
    for line in lines[-maxlen:]:
        history.append(line.rstrip("\n"))
    return history


def add_message(messenger: str, user_id: int, role: str, text: str) -> None:
    """Add a message to the user's conversation history."""
    key = f"{messenger}_{user_id}"
    if key not in _history:
        _history[key] = _load_history_from_disk(messenger, user_id)
    _history[key].append(f"{role}: {text}")


def get_context(messenger: str, user_id: int) -> str:
    """Return the conversation context as a single string (newline‑separated)."""
    key = f"{messenger}_{user_id}"
    if key not in _history:
        return ""
    return "\n".join(_history[key])