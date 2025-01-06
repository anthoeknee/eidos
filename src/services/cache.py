from typing import Optional, List, Dict, Set
import redis
from src.config import config
from src.utils import logger
from urllib.parse import urlparse
import socket


class CacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def set(self, key: str, value: str, expiry: Optional[int] = None):
        self.redis_client.set(key, value, ex=expiry)

    async def get(self, key: str) -> Optional[str]:
        value = self.redis_client.get(key)
        if value:
            return value.decode("utf-8")
        return None

    async def delete(self, key: str):
        self.redis_client.delete(key)

    async def clear(self):
        """Clear all keys from the cache."""
        self.redis_client.flushdb()

    # Hash operations
    async def hset(self, key: str, mapping: Dict[str, str]):
        """Set multiple key-value pairs in a hash."""
        self.redis_client.hset(key, mapping=mapping)

    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get a value from a hash by field."""
        return self.redis_client.hget(key, field)

    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all key-value pairs from a hash."""
        return self.redis_client.hgetall(key)

    async def hdel(self, key: str, *fields: str):
        """Delete one or more fields from a hash."""
        self.redis_client.hdel(key, *fields)

    # List operations
    async def lpush(self, key: str, *values: str):
        """Push one or more values to the head of a list."""
        self.redis_client.lpush(key, *values)

    async def rpush(self, key: str, *values: str):
        """Push one or more values to the tail of a list."""
        self.redis_client.rpush(key, *values)

    async def lrange(self, key: str, start: int, stop: int) -> List[str]:
        """Get a range of values from a list."""
        return self.redis_client.lrange(key, start, stop)

    async def lpop(self, key: str) -> Optional[str]:
        """Remove and get the first element in a list."""
        return self.redis_client.lpop(key)

    async def rpop(self, key: str) -> Optional[str]:
        """Remove and get the last element in a list."""
        return self.redis_client.rpop(key)

    # Set operations
    async def sadd(self, key: str, *values: str):
        """Add one or more members to a set."""
        self.redis_client.sadd(key, *values)

    async def smembers(self, key: str) -> Set[str]:
        """Get all members of a set."""
        return self.redis_client.smembers(key)

    async def srem(self, key: str, *values: str):
        """Remove one or more members from a set."""
        self.redis_client.srem(key, *values)


async def setup(bot):
    try:
        parsed_url = urlparse(config.REDIS_URL)

        # Configure Redis client
        redis_client = redis.Redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
            socket_timeout=10,
            retry_on_timeout=True,
        )

        # Test connection
        redis_client.ping()
        logger.info("Redis cache service initialized successfully")
        cache_service = CacheService(redis_client)
        return cache_service
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
