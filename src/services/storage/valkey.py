import json
from typing import Any, Dict, Optional, List, Set, Tuple
import valkey.asyncio as valkey
from src.core.config import settings
from src.services.storage.base import BaseStorageService
import asyncio
from valkey.exceptions import WatchError
import uuid
import numpy as np
import cohere
from valkey.commands.search.field import TagField, VectorField
from valkey.commands.search.indexDefinition import IndexDefinition, IndexType
from valkey.commands.search.query import Query

from src.utils.logger import Logger


class ValkeyService(BaseStorageService):
    """Valkey storage service implementation."""

    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)
        self._client: Optional[valkey.Valkey] = None
        self._pubsub = None
        self._cohere_client = (
            cohere.Client(settings.cohere_api_key) if settings.cohere_api_key else None
        )

    async def connect(self) -> None:
        """Connect to Valkey server."""
        logger = Logger(name="Valkey", level="INFO")
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                self._client = valkey.Valkey.from_url(
                    settings.valkey_url,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    decode_responses=True,
                    health_check_interval=30,
                )

                # Test connection
                async with asyncio.timeout(5):
                    if not await self._client.ping():
                        raise ConnectionError("Connection test failed")

                self._pubsub = self._client.pubsub()
                return

            except (ConnectionError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("Failed to connect to Valkey")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error connecting to Valkey: {str(e)}")
                raise

    async def disconnect(self) -> None:
        """Disconnect from Valkey server."""
        if self._pubsub:
            await self._pubsub.aclose()
        if self._client:
            await self._client.aclose()

    def _serialize(self, value: Any) -> str:
        """Serialize value to string"""
        return json.dumps(value)

    def _deserialize(self, value: Optional[str]) -> Any:
        """Deserialize value from string"""
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # If we can't decode as JSON, return the raw string
            return value

    # Core Key-Value Operations
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self._client:
            raise Exception("Not connected to Valkey")
        await self._client.set(key, self._serialize(value), ex=ttl)

    async def get(self, key: str) -> Any:
        """Get a value by key"""
        if not self._client:
            raise Exception("Not connected to Valkey")

        value = await self._client.get(key)
        return self._deserialize(value)

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

    async def atomic_update(
        self,
        key: str,
        update_func: callable,
        max_retries: int = 3,
        ttl: Optional[int] = None,
    ) -> Any:
        """Execute an atomic update operation with optimistic locking.

        Args:
            key: The key to update
            update_func: Callback that takes current value and returns new value
            max_retries: Maximum number of retry attempts
            ttl: Optional TTL in seconds
        """
        if not self._client:
            raise Exception("Not connected to Valkey")

        for attempt in range(max_retries):
            try:
                async with self._client.pipeline(transaction=True) as pipe:
                    await pipe.watch(key)

                    # Get and deserialize current value
                    current_value = await self.get(key)

                    # Get new value from update function
                    new_value = await update_func(current_value)

                    # Start transaction
                    pipe.multi()

                    # Serialize and set new value
                    await pipe.set(key, self._serialize(new_value))

                    if ttl is not None:
                        await pipe.expire(key, ttl)

                    await pipe.execute()
                    return new_value

            except WatchError:
                if attempt == max_retries - 1:
                    raise ValueError("Too many concurrent updates, try again later")
                await asyncio.sleep(0.1 * (attempt + 1))

    async def acquire_lock(self, lock_key: str, timeout: int = 10) -> bool:
        """Acquire a distributed lock.

        Args:
            lock_key: The lock key
            timeout: Lock timeout in seconds

        Returns:
            bool: True if lock was acquired, False otherwise
        """
        if not self._client:
            raise Exception("Not connected to Valkey")

        lock_value = str(uuid.uuid4())
        acquired = await self._client.set(
            f"lock:{lock_key}", lock_value, ex=timeout, nx=True
        )
        return bool(acquired)

    async def release_lock(self, lock_key: str) -> None:
        """Release a distributed lock."""
        if not self._client:
            raise Exception("Not connected to Valkey")

        await self._client.delete(f"lock:{lock_key}")

    # Vector Operations
    async def create_vector_index(
        self, index_name: str, vector_dimensions: int
    ) -> None:
        """Create a vector index."""
        if not self._client:
            raise Exception("Not connected to Valkey")
        try:
            # Check if index exists
            await self._client.ft(index_name).info()
            Logger(name="Valkey").info(f"Index {index_name} already exists!")
        except:
            # Schema
            schema = (
                TagField("tag"),
                VectorField(
                    "vector",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": vector_dimensions,
                        "DISTANCE_METRIC": "COSINE",
                    },
                ),
            )

            # Index Definition
            definition = IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH)

            # Create Index
            await self._client.ft(index_name).create_index(
                fields=schema, definition=definition
            )
            Logger(name="Valkey").info(f"Index {index_name} created successfully!")

    async def add_vector(
        self, index_name: str, key: str, vector: List[float], content: str, tag: str
    ) -> None:
        """Add a vector to the index."""
        if not self._client:
            raise Exception("Not connected to Valkey")

        await self._client.hset(
            f"doc:{key}",
            mapping={
                "vector": np.array(vector, dtype=np.float32).tobytes(),
                "content": content,
                "tag": tag,
            },
        )

    async def vector_knn_search(
        self, index_name: str, query_vector: List[float], top_k: int, tag: str
    ) -> List[Tuple[str, str, float]]:
        """Perform a KNN search on the vector index."""
        if not self._client:
            raise Exception("Not connected to Valkey")

        query = (
            Query(f"(@tag:{{ {tag} }})=>[KNN {top_k} @vector $vec as score]")
            .sort_by("score")
            .return_fields("content", "tag", "score")
            .paging(0, top_k)
            .dialect(2)
        )

        query_params = {"vec": np.array(query_vector, dtype=np.float32).tobytes()}
        results = await self._client.ft(index_name).search(query, query_params)

        return [(doc.id, doc.content, float(doc.score)) for doc in results.docs]

    async def vector_range_search(
        self, index_name: str, query_vector: List[float], radius: float, tag: str
    ) -> List[Tuple[str, str, float]]:
        """Perform a range search on the vector index."""
        if not self._client:
            raise Exception("Not connected to Valkey")

        query = (
            Query(
                f"(@tag:{{ {tag} }})=>[VECTOR_RANGE $radius $vec]=>{{$YIELD_DISTANCE_AS: score}}"
            )
            .sort_by("score")
            .return_fields("content", "tag", "score")
            .paging(
                0, 100
            )  # Valkey doesn't support top_k for range queries, so we fetch 100 and filter
            .dialect(2)
        )

        query_params = {
            "radius": radius,
            "vec": np.array(query_vector, dtype=np.float32).tobytes(),
        }
        results = await self._client.ft(index_name).search(query, query_params)

        return [(doc.id, doc.content, float(doc.score)) for doc in results.docs]

    async def generate_text_embedding(self, text: str) -> List[float]:
        """Generate text embeddings using Cohere."""
        if not self._cohere_client:
            raise Exception("Cohere API key not configured")
        response = await self._cohere_client.embed(texts=[text], model="small")
        return response.embeddings[0]

    async def generate_image_embedding(self, image_url: str) -> List[float]:
        """Generate image embeddings using Cohere."""
        if not self._cohere_client:
            raise Exception("Cohere API key not configured")
        response = await self._cohere_client.embed(
            texts=[image_url], model="multilingual-22-12", input_type="image-url"
        )
        return response.embeddings[0]
