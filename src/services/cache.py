from typing import Optional, Any, Union
import redis
from src.config import config
from src.utils import logger


class CacheService:
    def __init__(self, bot):
        self.bot = bot
        self.redis: Optional[redis.Redis] = None

    async def setup(self):
        """Initialize Redis connection."""
        try:
            self.redis = redis.Redis(
                url=config.REDIS_URL,
                password=config.REDIS_PASSWORD,
                decode_responses=True,  # Automatically decode responses to strings
            )
            # Test the connection
            self.redis.ping()
            logger.info("Redis cache service initialized successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Error setting up cache service: {e}")
            raise

    def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        try:
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key} from cache: {e}")
            return None

    def set(
        self, key: str, value: Union[str, int, float], ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache with optional TTL in seconds."""
        try:
            return self.redis.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Error setting key {key} in cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting key {key} from cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in cache."""
        try:
            return self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a numeric value in cache."""
        try:
            return self.redis.decr(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key}: {e}")
            return None

    def ttl(self, key: str) -> int:
        """Get the remaining TTL for a key in seconds."""
        try:
            return self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -2  # Redis returns -2 if the key doesn't exist

    def clear_all(self) -> bool:
        """Clear all keys from the cache."""
        try:
            return bool(self.redis.flushdb())
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


async def setup(bot):
    """Set up the cache service."""
    cache_service = CacheService(bot)
    await cache_service.setup()
    bot.cache = cache_service
