from dataclasses import dataclass
from typing import TypeVar, Generic, Optional
import time

T = TypeVar("T")


@dataclass
class Entry(Generic[T]):
    """Represents a single cache entry with its metadata."""

    value: T
    expiry: Optional[float] = None  # None means no expiration
    created_at: float = time.time()

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expiry is None:
            return False
        return time.time() > self.expiry
