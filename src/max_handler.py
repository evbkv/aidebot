# ==================== src/max_handler.py ====================
"""MAX messenger polling loop and message handling."""

import logging
import requests
import time
from .base_handler import MessengerHandler
from . import notifier

logger = logging.getLogger(__name__)


class MaxHandler(MessengerHandler):
    """Handler for MAX messenger."""

    def __init__(self, platform: str, owner_id: int, superuser_enabled: bool, token: str, api_base: str):
        super().__init__(platform, owner_id, superuser_enabled)
        self.token = token
        self.api_base = api_base
        self.headers = {"Authorization": token, "Content-Type": "application/json"}
        notifier.set_max_headers(self.headers)

    def send_message(self, chat_id: int, text: str) -> None:
        """Send a message to MAX (synchronous)."""
        self._send_message(chat_id, text)

    def get_user_language(self, update=None) -> str:
        """MAX does not provide language info; return default."""
        return 'ru'

    def _send_message(self, chat_id: int, text: str, retries: int = 3) -> None:
        """Low‑level message sending with retries."""
        url = f"{self.api_base}/messages?chat_id={chat_id}"
        data = {"text": text}
        for attempt in range(retries):
            try:
                r = requests.post(url, headers=self.headers, json=data, timeout=10)
                if r.status_code == 200:
                    logger.info(f"MAX send to {chat_id}: 200")
                    return
                elif r.status_code == 429:
                    time.sleep(1)
                    continue
                else:
                    logger.warning(f"MAX send status {r.status_code}")
                    return
            except requests.exceptions.Timeout:
                if attempt == retries - 1:
                    logger.error(f"MAX send timeout to {chat_id}")
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"MAX send error: {e}")
                return

    def run_polling(self) -> None:
        """Continuous polling loop for MAX messenger updates."""
        marker = None
        error_delay = 1

        while True:
            try:
                params = {"marker": marker} if marker else {}
                # fetch updates with retries
                for attempt in range(3):
                    try:
                        resp = requests.get(
                            f"{self.api_base}/updates",
                            headers=self.headers,
                            params=params,
                            timeout=35,
                        )
                        break
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"MAX updates attempt {attempt+1} failed: {e}")
                        if attempt == 2:
                            raise
                        time.sleep(1 * (attempt + 1))

                if resp.status_code != 200:
                    logger.warning(f"MAX updates status: {resp.status_code}")
                    time.sleep(error_delay)
                    error_delay = min(error_delay * 2, 30)
                    continue

                error_delay = 1
                data = resp.json()
                updates = data.get("updates", []) if isinstance(data, dict) else []
                marker = data.get("marker") if isinstance(data, dict) else None

                for event in updates:
                    if event.get("update_type") != "message_created":
                        continue
                    msg = event.get("message", {})
                    chat_id = msg.get("recipient", {}).get("chat_id")
                    text = msg.get("body", {}).get("text")
                    user_id = msg.get("sender", {}).get("user_id")
                    if not all([chat_id, text, user_id]):
                        continue

                    # Validation is done inside process_message via storage.log_message
                    user_name = msg.get("sender", {}).get("name", "Unknown")

                    # /restart handling
                    if text.startswith("/restart") and user_id == self.owner_id and self.superuser_enabled:
                        self.send_message(chat_id, "Command not supported")
                        continue

                    self.process_message(
                        user_id=user_id,
                        chat_id=chat_id,
                        text=text,
                        user_name=user_name,
                        update=None,
                    )

            except requests.exceptions.Timeout:
                logger.warning("MAX polling timeout")
                time.sleep(error_delay)
            except Exception as e:
                logger.exception(f"MAX polling error: {e}")
                time.sleep(error_delay)
            # no extra sleep – long polling already has timeout