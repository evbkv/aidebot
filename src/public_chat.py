# ==================== src/public_chat.py ====================
"""Handle public (non‑owner) user messages: persona loading, caching, prompt building."""

import os
import hashlib
import logging
from . import llm, prompts, cache, context

logger = logging.getLogger(__name__)

_persona = None
_persona_mtime = 0


def _load_persona() -> str:
    """Load the persona text from file, caching it and tracking modification time."""
    global _persona, _persona_mtime
    from config import USER_INFO_FILE

    mtime = os.path.getmtime(USER_INFO_FILE) if os.path.exists(USER_INFO_FILE) else 0
    if mtime != _persona_mtime:
        with open(USER_INFO_FILE, "r", encoding="utf-8") as f:
            _persona = f.read().strip()
        _persona_mtime = mtime
        cache.invalidate()  # persona changed → invalidate all cached answers
    return _persona


def answer_for_public(text: str, user_id: int, platform: str, ctx: str = None, lang: str = 'ru') -> str:
    """Generate a response for a public user, using persona and conversation context."""
    persona = _load_persona()
    # build cache key from hashed parts to keep it short
    key_parts = [
        hashlib.md5(text.encode()).hexdigest(),
        hashlib.md5(persona.encode()).hexdigest(),
        hashlib.md5((ctx or "").encode()).hexdigest(),
    ]
    key = "".join(key_parts)
    cached = cache.get(key)
    if cached:
        return cached

    prompt = prompts.create_public_prompt(text, persona)
    if ctx:
        prompt = prompts.add_context(prompt, ctx)

    # Note: lang could be used to adjust the prompt (e.g., add "Answer in {lang}")
    # but we keep the original prompt as is for now.
    answer = llm.ask(prompt)
    cache.set(key, answer)
    return answer