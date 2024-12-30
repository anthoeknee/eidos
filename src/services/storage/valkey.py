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
        self._url = settings.valkey_url or "valkey://192.168.0.223:6379"
        self.index_name = "chat_vectors"
        self.doc_prefix = "doc:"
        self.vector_dimensions = 1536  # Standard for many embedding models
        self.logger = Logger(name="ValkeyService")

    async def connect(self) -> None:
        """Connect to Valkey and initialize vector index."""
        try:
            self._client = await valkey.Valkey.from_url(self._url)
            await self._create_vector_index()
            self.logger.info("Connected to Valkey and initialized vector index")
        except Exception as e:
            self.logger.error(f"Failed to connect to Valkey: {e}")
            raise

    async def _create_vector_index(self) -> None:
        """Initialize vector storage using basic key-value functionality."""
        try:
            # Create a simple key to mark that we've initialized
            index_key = f"{self.index_name}:initialized"
            if not await self._client.exists(index_key):
                await self._client.set(index_key, "1")
                self.logger.info("Initialized vector storage")
            else:
                self.logger.info("Vector storage already initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector storage: {str(e)}")
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
    async def add_vector(
        self, index_name: str, key: str, vector: List[float], content: str, tag: str
    ) -> None:
        """Store vector data using basic hash storage."""
        if not self._client:
            raise Exception("Not connected to Valkey")

        vector_data = {
            "vector": json.dumps(vector),  # Store vector as JSON string
            "content": content,
            "tag": tag,
        }

        await self._client.hmset(f"{self.doc_prefix}{key}", vector_data)

    async def vector_knn_search(
        self, index_name: str, query_vector: List[float], top_k: int, tag: str
    ) -> List[Tuple[str, str, float]]:
        """Basic vector search implementation using brute force comparison."""
        if not self._client:
            raise Exception("Not connected to Valkey")

        # Get all keys with the document prefix
        keys = await self._client.keys(f"{self.doc_prefix}*")
        results = []

        # Fetch and compare vectors
        for key in keys:
            data = await self._client.hgetall(key)
            if data and data.get("tag") == tag:
                stored_vector = json.loads(data.get("vector", "[]"))
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_vector, stored_vector)
                results.append((key, data.get("content", ""), similarity))

        # Sort by similarity and return top k results
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2) if norm1 and norm2 else 0.0

    async def vector_range_search(
        self, index_name: str, query_vector: List[float], radius: float, tag: str
    ) -> List[Tuple[str, str, float]]:
        """Implement vector range search."""
        vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()

        # Use FT.SEARCH with range syntax
        query = f"(@tag:{{{tag}}})" f"[VECTOR_RANGE {radius} @vector $vec AS score]"

        results = await self._client.ft(index_name).search(
            query, {"vec": vector_bytes}, dialect=2
        )

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

    async def create_vector_index(
        self, index_name: str, vector_dimensions: int
    ) -> None:
        """Implement the abstract method from BaseStorageService."""
        self.index_name = index_name
        self.vector_dimensions = vector_dimensions
        await self._create_vector_index()

    async def disconnect(self) -> None:
        """Implement disconnect method."""
        if self._client:
            await self._client.close()
            self._client = None
