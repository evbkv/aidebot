# ==================== src/dispatcher.py ====================
"""Main dispatcher: routes messages to commands or AI, checks owner privileges."""

from . import llm, public_chat, utils, context, calc
from gigachat.exceptions import GigaChatException
from config import TELEGRAM_ALLOWED_USER_ID, TELEGRAM_SUPERUSER_ENABLED, MAX_ALLOWED_USER_ID, MAX_SUPERUSER_ENABLED
import os
import logging
from .i18n import get_text

logger = logging.getLogger(__name__)


def _is_owner(user_id: int, owner_id: int, platform: str) -> bool:
    """Determine if the user is the owner for the given platform."""
    if platform == "telegram":
        return (user_id == owner_id) and TELEGRAM_SUPERUSER_ENABLED
    elif platform == "max":
        return (user_id == owner_id) and MAX_SUPERUSER_ENABLED
    return user_id == owner_id


def _handle_command(cmd: str, args: list, user_id: int, owner_id: int, platform: str, is_owner: bool, lang: str) -> str:
    """Process a command (starts with '/') and return the answer."""
    cmd = cmd.lower()
    if cmd == "start":
        if is_owner:
            return get_text("start_owner", lang)
        return get_text("start_public", lang)
    elif cmd == "help":
        if is_owner:
            return get_text("help_owner", lang)
        return get_text("help_public", lang)
    elif cmd == "id":
        if is_owner:
            return get_text("id_response", lang, user_id=user_id)
        return get_text("id_denied", lang)
    elif cmd.startswith("summary"):
        if not is_owner:
            return get_text("id_denied", lang)
        if len(args) != 2:
            return get_text("summary_usage", lang)
        messenger, uid = args[0], args[1]
        if messenger not in ("telegram", "max", "web"):
            return get_text("summary_invalid_messenger", lang)
        if not uid.isdigit():
            return get_text("summary_invalid_uid", lang)
        path = f"chats/{messenger}/{uid}.txt"
        if not os.path.exists(path):
            return get_text("summary_not_found", lang)
        with open(path, "r", encoding="utf-8") as f:
            dialog = f.read()
        return llm.summarize(dialog)
    else:
        return get_text("unknown_command", lang)


def handle_incoming(text: str, user_id: int, owner_id: int, platform: str, lang: str = 'ru') -> dict:
    """Main entry point: route message to command handler or AI, return answer with metadata."""
    is_owner = _is_owner(user_id, owner_id, platform)
    try:
        if text.startswith("/"):
            parts = text.strip().split()
            cmd = parts[0][1:]
            args = parts[1:]
            answer = _handle_command(cmd, args, user_id, owner_id, platform, is_owner, lang)
        else:
            ctx = context.get_context(platform, user_id)
            if is_owner:
                answer = llm.ask(text)
            else:
                answer = public_chat.answer_for_public(text, user_id, platform, ctx, lang)
            answer = utils.clean_text(answer)
        split = len(answer) > 4000
        error = False
        markdown = False
    except GigaChatException:
        answer = get_text("gigachat_error", lang)
        split = False
        error = True
        markdown = False
        logger.exception("GigaChat error in dispatcher")
    except Exception:
        answer = get_text("internal_error", lang)
        split = False
        error = True
        markdown = False
        logger.exception("Unexpected error in dispatcher")
    return {"text": answer, "split": split, "error": error, "markdown": markdown}