# ==================== src/base_handler.py ====================
"""Abstract base class for messenger handlers."""

from abc import ABC, abstractmethod
import logging
from . import dispatcher, context, storage, utils
from .i18n import get_text

logger = logging.getLogger(__name__)


class MessengerHandler(ABC):
    """Base class for all messenger handlers.

    Subclasses must implement send_message, get_user_language, and run_polling.
    """

    def __init__(self, platform: str, owner_id: int, superuser_enabled: bool):
        self.platform = platform
        self.owner_id = owner_id
        self.superuser_enabled = superuser_enabled

    @abstractmethod
    def send_message(self, chat_id: int, text: str) -> None:
        """Send a message to a specific chat."""
        pass

    @abstractmethod
    def get_user_language(self, update) -> str:
        """Extract user language code from the update object."""
        return 'ru'  # default

    def process_message(self, user_id: int, chat_id: int, text: str, user_name: str, update=None) -> None:
        """Common message processing logic: rate limit, context, logging, dispatch, reply."""
        lang = self.get_user_language(update)
        if utils.is_rate_limited(user_id):
            self.send_message(chat_id, get_text("rate_limit", lang))
            return

        context.add_message(self.platform, user_id, 'user', text)
        storage.log_message(self.platform, user_id, 'user', text, user_name)

        result = dispatcher.handle_incoming(text, user_id, self.owner_id, self.platform, lang)
        answer = result['text']

        context.add_message(self.platform, user_id, 'bot', answer)
        storage.log_message(self.platform, user_id, 'bot', answer)

        # Use universal long message sender
        utils.send_long_message(
            chat_id=chat_id,
            text=answer,
            split_needed=result['split'],
            send_func=self.send_message,
            platform=self.platform,
        )

    @abstractmethod
    def run_polling(self) -> None:
        """Start the polling loop for this messenger."""
        pass