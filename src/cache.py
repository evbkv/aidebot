# ==================== src/cache.py ====================
"""Simple in‑memory cache with time‑to‑live (TTL)."""

import time

_cache = {}
_ttl = 300  # seconds


def get(key: str):
    """Retrieve value from cache if it exists and is not expired."""
    if key in _cache:
        value, ts = _cache[key]
        if time.time() - ts < _ttl:
            return value
        # expired
        del _cache[key]
    return None


def set(key: str, value) -> None:
    """Store value in cache with current timestamp."""
    _cache[key] = (value, time.time())


def invalidate() -> None:
    """Clear the entire cache."""
    _cache.clear()