from redis import Redis
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from urllib.parse import urlparse
import logging
from typing import Optional, Dict, List, Set

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self, redis_client: Redis):
        """Initialize the cache service with a Redis client."""
        self.redis_client = redis_client

    @classmethod
    def create_from_url(cls, redis_url: str) -> "CacheService":
        """Create a new CacheService instance from a Redis URL."""
        try:
            parsed_url = urlparse(redis_url)

            # Extract authentication details
            if "@" in parsed_url.netloc:
                auth_part, host_part = parsed_url.netloc.split("@")
                if ":" in auth_part:
                    _, password = auth_part.split(":")
                else:
                    password = auth_part
            else:
                password = None
                host_part = parsed_url.netloc

            # Extract host and port
            if ":" in host_part:
                host, port = host_part.split(":")
                port = int(port)
            else:
                host = host_part
                port = 6379

            retry_strategy = Retry(
                backoff=ExponentialBackoff(cap=10, base=1),
                retries=3,
                supported_errors=(ConnectionError, TimeoutError),
            )

            redis_client = Redis(
                host=host,
                port=port,
                password=password,
                retry_on_timeout=True,
                retry=retry_strategy,
                socket_keepalive=True,
                health_check_interval=30,
            )

            # Test connection
            redis_client.ping()
            logger.info(f"Successfully connected to Redis at {host}:{port}")

            return cls(redis_client)

        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            raise

    async def set(self, key: str, value: str, expiry: int = None):
        try:
            self.redis_client.set(key, value, ex=expiry)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error: {e}")
            # Attempt to reconnect
            self.redis_client.ping()
            # Retry the operation
            self.redis_client.set(key, value, ex=expiry)

    async def get(self, key: str) -> Optional[str]:
        try:
            value = self.redis_client.get(key)
            return value.decode("utf-8") if value else None
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error: {e}")
            return None

    async def delete(self, key: str):
        try:
            self.redis_client.delete(key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error: {e}")

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
    """Setup the cache service."""
    try:
        from src.config import get_config

        config = get_config()

        redis_url = config.REDIS_URL
        cache_service = CacheService.create_from_url(redis_url)
        logger.info("Redis cache service initialized successfully")
        return cache_service
    except Exception as e:
        logger.error(f"Failed to initialize Redis cache service: {e}")
        raise
