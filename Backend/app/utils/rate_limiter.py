"""Simple in-memory rate limiter for login endpoints"""
import time
import hashlib
from collections import defaultdict
from fastapi import HTTPException, status


class RateLimiter:
    """Sliding window rate limiter"""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts = defaultdict(list)

    def _key(self, identifier: str) -> str:
        return identifier

    def check(self, identifier: str) -> bool:
        """Check if the identifier is rate limited. Returns True if allowed."""
        key = self._key(identifier)
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self._attempts[key] = [t for t in self._attempts[key] if t > window_start]

        if len(self._attempts[key]) >= self.max_attempts:
            return False

        self._attempts[key].append(now)
        return True

    def reset(self, identifier: str):
        """Reset rate limit for an identifier."""
        key = self._key(identifier)
        self._attempts.pop(key, None)


# Per-IP rate limiter: 5 attempts per 60 seconds
login_limiter = RateLimiter(max_attempts=5, window_seconds=60)


def get_client_ip(request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
