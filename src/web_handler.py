# ==================== src/web_handler.py ====================
"""Web widget handler: provides HTTP endpoints for a chat widget."""

import logging
import uuid
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import threading
from .base_handler import MessengerHandler
from . import dispatcher, context, storage, utils

logger = logging.getLogger(__name__)

# In‑memory session store (for production replace with Redis/database)
_sessions = {}  # session_id -> {"name": str, "phone": str, "user_id": int}


class WebHandler(MessengerHandler):
    """Handler for web widget messages."""

    def __init__(self, platform: str, owner_id: int, superuser_enabled: bool,
                 host: str, port: int, allowed_origins: list):
        super().__init__(platform, owner_id, superuser_enabled)
        self.host = host
        self.port = port
        self.allowed_origins = allowed_origins
        self.app = Flask(__name__)
        CORS(self.app, origins=allowed_origins, supports_credentials=True)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/api/start', methods=['POST'])
        def start_session():
            """First request: expects JSON with name and phone.
            Returns a session_id cookie and stores user info.
            """
            data = request.get_json()
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            if not name:
                return jsonify({"error": "Name is required"}), 400
            phone = data.get('phone', '').strip()

            session_id = str(uuid.uuid4())
            # Generate a numeric user_id from session_id (simple hash)
            user_id = hash(session_id) % (10**10)

            _sessions[session_id] = {
                "name": name,
                "phone": phone,
                "user_id": user_id
            }

            response = jsonify({"status": "ok", "session_id": session_id})
            response.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
            return response

        @self.app.route('/api/message', methods=['POST'])
        def handle_message():
            """Process a message from the widget. Expects session_id in cookie or JSON.
            Returns bot's reply.
            """
            session_id = request.cookies.get('session_id') or request.json.get('session_id')
            if not session_id or session_id not in _sessions:
                return jsonify({"error": "Invalid or missing session"}), 401

            session = _sessions[session_id]
            user_id = session['user_id']
            user_name = session['name']
            user_phone = session['phone']

            data = request.get_json()
            text = data.get('text', '').strip()
            if not text:
                return jsonify({"error": "Empty message"}), 400

            lang = 'ru'

            # Rate limiting
            if utils.is_rate_limited(user_id):
                return jsonify({"error": "Rate limit exceeded"}), 429

            # Log user message with phone
            context.add_message(self.platform, user_id, 'user', text)
            storage.log_message(self.platform, user_id, 'user', text, user_name, user_phone)

            # Get answer from dispatcher
            result = dispatcher.handle_incoming(text, user_id, self.owner_id, self.platform, lang)
            answer = result['text']

            # Log bot message
            context.add_message(self.platform, user_id, 'bot', answer)
            storage.log_message(self.platform, user_id, 'bot', answer)

            return jsonify({"reply": answer})

        @self.app.route('/api/end', methods=['POST'])
        def end_session():
            """Optionally clear session data."""
            session_id = request.cookies.get('session_id')
            if session_id and session_id in _sessions:
                del _sessions[session_id]
            response = jsonify({"status": "ok"})
            response.delete_cookie('session_id')
            return response

    def send_message(self, chat_id: int, text: str) -> None:
        """Not used for web handler because replies are sent directly via HTTP."""
        pass

    def get_user_language(self, update=None) -> str:
        return 'ru'

    def run_polling(self) -> None:
        """Start the Flask server."""
        logger.info(f"Starting web widget server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, threaded=True)