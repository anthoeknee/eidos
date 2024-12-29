import json
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
from src.services.storage.valkey import ValkeyService
from src.utils.logger import Logger
from src.core import settings
import uuid
from google.genai import Client


class MemoryService:
    """
    Manages the storage, retrieval, and manipulation of memories.
    """

    def __init__(self, valkey: ValkeyService):
        self.valkey = valkey
        self.logger = Logger(name="MemoryService", level="INFO")
        self.model = "gemini-2.0-flash-exp"
        self.client = None

    async def connect(self):
        """Connect to the memory service."""
        self.logger.info("Memory service connected.")
        # Initialize the google client
        # self.client = Client(api_key=settings.google_api_key)

    async def disconnect(self):
        """Disconnect from the memory service."""
        self.logger.info("Memory service disconnected.")

    def _get_key(self, category: str, memory_id: Optional[str] = None) -> str:
        """Construct a key for valkey."""
        if memory_id:
            return f"memory:{category}:{memory_id}"
        return f"memory:{category}"

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

    async def create_memory(
        self,
        category: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Adds a new memory to the system."""
        memory_id = str(uuid.uuid4())
        key = self._get_key(category, memory_id)
        timestamp = datetime.now().isoformat()
        memory_data = {
            "id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": timestamp,
        }
        await self.valkey.set(key, self._serialize(memory_data))
        self.logger.debug(f"Created memory {memory_id} in category {category}")
        return memory_id

    async def create_unique_memory(
        self,
        category: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Adds a new memory if no similar memory exists."""
        existing_memories = await self.search_memory(category, content)
        if existing_memories:
            self.logger.debug(
                f"Similar memory already exists in category {category}, not creating."
            )
            return None
        return await self.create_memory(category, content, metadata)

    async def create_alternative_memory(
        self,
        category: str,
        original_memory_id: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Adds a new alternative memory version."""
        memory_id = str(uuid.uuid4())
        key = self._get_key(category, memory_id)
        timestamp = datetime.now().isoformat()
        memory_data = {
            "id": memory_id,
            "original_memory_id": original_memory_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": timestamp,
        }
        await self.valkey.set(key, self._serialize(memory_data))
        self.logger.debug(
            f"Created alternative memory {memory_id} for {original_memory_id} in category {category}"
        )
        return memory_id

    async def get_memory(self, category: str, memory_id: str) -> Optional[Dict]:
        """Retrieves a specific memory by its ID."""
        key = self._get_key(category, memory_id)
        memory_data = await self.valkey.get(key)
        if memory_data:
            self.logger.debug(f"Retrieved memory {memory_id} from category {category}")
            return self._deserialize(memory_data)
        self.logger.debug(f"Memory {memory_id} not found in category {category}")
        return None

    async def get_memories(self, category: str) -> List[Dict]:
        """Retrieves all memories in a specific category."""
        key = self._get_key(category)
        all_keys = await self.valkey._client.keys(f"{key}:*")
        memories = []
        for k in all_keys:
            memory_data = await self.valkey.get(k)
            if memory_data:
                memories.append(self._deserialize(memory_data))
        self.logger.debug(
            f"Retrieved {len(memories)} memories from category {category}"
        )
        return memories

    async def get_last_message(self, category: str) -> Optional[Dict]:
        """Retrieves the most recent message in a category."""
        memories = await self.get_memories(category)
        if not memories:
            return None
        sorted_memories = sorted(
            memories, key=lambda x: x.get("timestamp", ""), reverse=True
        )
        self.logger.debug(f"Retrieved last message from category {category}")
        return sorted_memories[0]

    async def update_memory(
        self,
        category: str,
        memory_id: str,
        content: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Updates an existing memory with new content or metadata."""
        key = self._get_key(category, memory_id)
        memory_data = await self.get_memory(category, memory_id)
        if not memory_data:
            self.logger.debug(
                f"Memory {memory_id} not found in category {category}, cannot update."
            )
            return False

        if content is not None:
            memory_data["content"] = content
        if metadata:
            memory_data["metadata"].update(metadata)

        await self.valkey.set(key, self._serialize(memory_data))
        self.logger.debug(f"Updated memory {memory_id} in category {category}")
        return True

    async def delete_memory(self, category: str, memory_id: str) -> bool:
        """Removes a specific memory by its ID."""
        key = self._get_key(category, memory_id)
        if await self.valkey.get(key):
            await self.valkey.delete(key)
            self.logger.debug(f"Deleted memory {memory_id} from category {category}")
            return True
        self.logger.debug(f"Memory {memory_id} not found in category {category}")
        return False

    async def delete_similar_memories(self, category: str, content: Any) -> int:
        """Removes memories similar to specified content."""
        memories = await self.search_memory(category, content)
        deleted_count = 0
        for memory in memories:
            if await self.delete_memory(category, memory["id"]):
                deleted_count += 1
        self.logger.debug(
            f"Deleted {deleted_count} similar memories from category {category}"
        )
        return deleted_count

    async def search_memory(
        self,
        category: str,
        search_term: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """Searches for memories based on a search term and other criteria."""
        memories = await self.get_memories(category)
        results = []
        for memory in memories:
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})
            if search_term.lower() in str(
                content
            ).lower() and self._check_metadata_filters(metadata, metadata_filters):
                results.append(memory)
        self.logger.debug(
            f"Found {len(results)} memories in category {category} matching search term '{search_term}'"
        )
        return results

    def _check_metadata_filters(
        self, metadata: Dict, metadata_filters: Optional[Dict]
    ) -> bool:
        """Helper function to check if metadata matches filters."""
        if not metadata_filters:
            return True
        for key, value in metadata_filters.items():
            if metadata.get(key) != value:
                return False
        return True

    async def search_memory_by_date(self, category: str, date: str) -> List[Dict]:
        """Searches for memories created on a specific date."""
        memories = await self.get_memories(category)
        results = [
            memory
            for memory in memories
            if memory.get("timestamp", "").startswith(date)
        ]
        self.logger.debug(
            f"Found {len(results)} memories in category {category} created on {date}"
        )
        return results

    async def count_memories(self, category: str) -> int:
        """Counts the number of memories in a category."""
        memories = await self.get_memories(category)
        count = len(memories)
        self.logger.debug(f"Counted {count} memories in category {category}")
        return count

    async def wipe_category(self, category: str) -> None:
        """Deletes all memories in a specific category."""
        key = self._get_key(category)
        all_keys = await self.valkey._client.keys(f"{key}:*")
        for k in all_keys:
            await self.valkey.delete(k)
        self.logger.debug(f"Wiped all memories in category {category}")

    async def wipe_all_memories(self) -> None:
        """Deletes all memories across all categories."""
        all_keys = await self.valkey._client.keys("memory:*")
        for k in all_keys:
            await self.valkey.delete(k)
        self.logger.debug("Wiped all memories across all categories")

    def count_tokens(self, content: str) -> int:
        """Count tokens for given content"""
        if not self.client:
            self.client = Client(api_key=settings.google_api_key)
        response = self.client.models.count_tokens(model=self.model, contents=content)
        return response.total_tokens

    async def start(self) -> None:
        """Start the service."""
        await self.connect()
        self.logger.info("Memory service started.")

    async def stop(self) -> None:
        """Stop the service."""
        await self.disconnect()
        self.logger.info("Memory service stopped.")

    async def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return True
