# ==================== config.py ====================
# Configuration file for AideBot.
# All sensitive data should be kept here (tokens, IDs, etc.).
# Note: In production, consider using environment variables.

# LLM provider selection
LLM_PROVIDER = "gigachat"   # Options: "gigachat"

GIGACHAT_CREDENTIALS = "" # GigaChat API credentials
USER_INFO_FILE = "persona.txt" # File containing the persona description

LOG_TO_FILE = False   # Set to False to disable writing logs to bot.log

# Telegram settings
TELEGRAM_ENABLED = False # Enable Telegram integration
TELEGRAM_BOT_TOKEN = "" # Telegram bot token
TELEGRAM_ALLOWED_USER_ID = 0 # Owner's Telegram user ID
TELEGRAM_SUPERUSER_ENABLED = True # Allow owner commands in Telegram

# MAX settings
MAX_ENABLED = False # Enable MAX messenger integration
MAX_BOT_TOKEN = "" # MAX bot token
MAX_ALLOWED_USER_ID = 0 # Owner's MAX user ID
MAX_SUPERUSER_ENABLED = False # Allow owner commands in MAX
MAX_API_BASE = "https://platform-api.max.ru" # MAX API base URL

# Web widget settings
WEB_ENABLED = True # Enable web widget
WEB_HOST = "0.0.0.0" # Listen on all interfaces (behind reverse proxy)
WEB_PORT = 5000  # Port for Flask
WEB_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "null"
]