import json
from typing import Any, Dict, Optional, List, Set
import redis.asyncio as redis
from src.core.config import settings
from src.services.storage.base import BaseStorageService
import asyncio


class ValkeyService(BaseStorageService):
    """Valkey storage service implementation using Redis protocol compatibility.

    Valkey is a Redis-compatible database that can be accessed using Redis clients.
    This implementation uses the redis-py async client to communicate with Valkey.
    """

    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)
        self._client: Optional[redis.Redis] = None
        self._pubsub = None

    async def connect(self) -> None:
        """Connect to Valkey server using Redis protocol."""
        from src.utils.logger import Logger

        logger = Logger(name="Valkey", level="INFO")

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Connection attempt {attempt + 1} to Valkey at {settings.valkey_url}"
                )

                # Create Redis client
                self._client = redis.Redis.from_url(
                    settings.valkey_url,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    decode_responses=True,
                    health_check_interval=30,
                )

                # Test connection with explicit timeout
                logger.debug("Testing Valkey connection...")
                try:
                    async with asyncio.timeout(5):
                        ping_result = await self._client.ping()
                        logger.debug(f"Ping result: {ping_result}")
                        if not ping_result:
                            raise ConnectionError("Valkey ping returned False")
                except asyncio.TimeoutError:
                    logger.error(f"Ping timeout on attempt {attempt + 1}")
                    raise

                # Initialize pubsub if ping successful
                self._pubsub = self._client.pubsub()
                logger.info("Successfully connected to Valkey")
                return

            except (ConnectionError, asyncio.TimeoutError) as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.debug(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("All connection attempts failed")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

    async def disconnect(self) -> None:
        """Disconnect from Valkey server."""
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.close()

    def _serialize(self, value: Any) -> str:
        """Serialize value to string."""
        return json.dumps(value) if not isinstance(value, str) else value

    def _deserialize(self, value: Optional[bytes]) -> Any:
        """Deserialize value from bytes."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.decode("utf-8")

    # Core Key-Value Operations
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self._client:
            raise Exception("Not connected to Valkey")
        await self._client.set(key, self._serialize(value), ex=ttl)

    async def get(self, key: str) -> Optional[Any]:
        if not self._client:
            raise Exception("Not connected to Valkey")
        return self._deserialize(await self._client.get(key))

    async def delete(self, key: str) -> None:
        if not self._client:
            raise Exception("Not connected to Valkey")
        await self._client.delete(key)

    # List Operations
    async def list_push(self, key: str, value: Any, right: bool = True) -> None:
        if not self._client:
            raise Exception("Not connected to Valkey")
        if right:
            await self._client.rpush(key, self._serialize(value))
        else:
            await self._client.lpush(key, self._serialize(value))

    async def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        if not self._client:
            raise Exception("Not connected to Valkey")
        values = await self._client.lrange(key, start, end)
        return [self._deserialize(v) for v in values]

    # Set Operations
    async def set_add(self, key: str, *values: Any) -> None:
        if not self._client:
            raise Exception("Not connected to Valkey")
        serialized = [self._serialize(v) for v in values]
        await self._client.sadd(key, *serialized)

    async def set_members(self, key: str) -> Set[Any]:
        if not self._client:
            raise Exception("Not connected to Valkey")
        members = await self._client.smembers(key)
        return {self._deserialize(m) for m in members}

    # Hash Operations
    async def hash_set(self, key: str, field: str, value: Any) -> None:
        if not self._client:
            raise Exception("Not connected to Valkey")
        await self._client.hset(key, field, self._serialize(value))

    async def hash_get(self, key: str, field: str) -> Optional[Any]:
        if not self._client:
            raise Exception("Not connected to Valkey")
        return self._deserialize(await self._client.hget(key, field))

    # Pub/Sub Operations
    async def publish(self, channel: str, message: Any) -> None:
        if not self._client:
            raise Exception("Not connected to Valkey")
        await self._client.publish(channel, self._serialize(message))

    async def subscribe(self, channel: str, callback: callable) -> None:
        if not self._pubsub:
            raise Exception("Not connected to Valkey")
        await self._pubsub.subscribe(channel)
        while True:
            message = await self._pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await callback(self._deserialize(message["data"]))

    async def is_healthy(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    # Add these methods to implement BaseService
    async def start(self) -> None:
        """Start the service by connecting to Valkey."""
        await self.connect()

    async def stop(self) -> None:
        """Stop the service by disconnecting from Valkey."""
        await self.disconnect()
