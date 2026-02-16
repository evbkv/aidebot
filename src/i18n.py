# ==================== src/i18n.py ====================
"""Internationalization support: load translations from JSON files."""

import json
import os

_translations = {}


def get_text(key: str, lang: str = 'en', **kwargs) -> str:
    """Return localized string for the given key and language.

    Args:
        key: Translation key.
        lang: Language code (e.g., 'ru', 'en').
        **kwargs: Format parameters to insert into the string.

    Returns:
        Localized string, or the key itself if not found.
    """
    if lang not in _translations:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'locales', f'{lang}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                _translations[lang] = json.load(f)
        else:
            _translations[lang] = {}  # fallback empty
    text = _translations[lang].get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text