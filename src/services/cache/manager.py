import time
from typing import Any, Dict, Optional, TypeVar

from ..base import BaseService
from .types import Entry

T = TypeVar("T")


class Manager(BaseService):
    """
    A flexible in-memory cache manager that can store any type of data.
    Supports expiration and automatic cleanup of expired entries.
    """

    def __init__(self, default_ttl: Optional[float] = None):
        """
        Initialize the cache manager.

        Args:
            default_ttl: Default time-to-live in seconds for cache entries.
                        None means entries never expire by default.
        """
        super().__init__()
        self._store: Dict[str, Entry] = {}
        self.default_ttl = default_ttl

    async def initialize(self) -> None:
        """Initialize the cache manager."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the cache manager."""
        self._store.clear()
        await super().cleanup()

    def _calculate_expiry(self, ttl: Optional[float]) -> Optional[float]:
        """Calculate the expiry timestamp based on TTL."""
        if ttl is None:
            ttl = self.default_ttl
        if ttl is None:
            return None
        return time.time() + ttl

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key
            value: The value to store
            ttl: Time-to-live in seconds. None uses the default TTL.
        """
        self.ensure_initialized()
        expiry = self._calculate_expiry(ttl)
        self._store[key] = Entry(value=value, expiry=expiry)

    def get(self, key: str, default: Any = None) -> Optional[T]:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key
            default: Value to return if key not found or expired

        Returns:
            The cached value or default if not found/expired
        """
        self.ensure_initialized()
        entry = self._store.get(key)

        if entry is None:
            return default

        if entry.is_expired:
            del self._store[key]
            return default

        return entry.value

    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        self.ensure_initialized()
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.ensure_initialized()
        self._store.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        self.ensure_initialized()
        expired_keys = [key for key, entry in self._store.items() if entry.is_expired]

        for key in expired_keys:
            del self._store[key]

        return len(expired_keys)

    @property
    def size(self) -> int:
        """Get the current number of entries in the cache."""
        return len(self._store)
