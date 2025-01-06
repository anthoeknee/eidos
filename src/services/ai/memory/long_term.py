from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy import text
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    channel_id: str
    content: str
    embedding: List[float]
    memory_type: str
    metadata: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class LongTermMemory:
    def __init__(self, bot):
        self.bot = bot
        self.memory_buffer = {}
        self.last_processed = {}
        self.min_messages_for_processing = 3
        self.processing_interval = timedelta(minutes=10)
        self.memory_categories = {
            "conversation": 0.7,
            "important": 0.8,
            "image": 0.6,
        }

    async def add_to_buffer(self, channel_id: str, content: str):
        """Add a message to the memory buffer."""
        if channel_id not in self.memory_buffer:
            self.memory_buffer[channel_id] = []
            # Initialize last_processed time when creating a new buffer
            self.last_processed[channel_id] = datetime.utcnow()

        self.memory_buffer[channel_id].append(content)

        # Only check for processing if we have enough messages
        if len(self.memory_buffer[channel_id]) >= self.min_messages_for_processing:
            await self._check_process_memory(channel_id)

    async def _check_process_memory(self, channel_id: str):
        """Check if memories should be processed for a channel."""
        try:
            current_time = datetime.utcnow()
            last_processed = self.last_processed.get(channel_id)
            buffer_messages = self.memory_buffer.get(channel_id, [])

            # Only process if we have enough messages AND enough time has passed
            should_process = len(
                buffer_messages
            ) >= self.min_messages_for_processing and (
                not last_processed
                or current_time - last_processed >= self.processing_interval
            )

            if should_process:
                await self._process_and_store_memories(channel_id)

        except Exception as e:
            logger.error(f"Error checking memory processing: {e}")

    async def _process_and_store_memories(self, channel_id: str):
        """Process and store memories from the buffer."""
        try:
            messages = self.memory_buffer.get(channel_id, [])
            if not messages:
                return

            memory_text = "\n".join(messages)

            # Generate embeddings
            embeddings = await self.cohere.generate(
                inputs=[memory_text], input_type="search_document"
            )

            if not embeddings:
                logger.error(f"Failed to generate embeddings for channel {channel_id}")
                return

            # Analyze importance
            importance_score = await self._analyze_importance(memory_text)
            memory_type = "important" if importance_score > 0.8 else "conversation"

            # Create memory object
            memory = Memory(
                channel_id=channel_id,
                content=memory_text,
                embedding=embeddings[0],
                memory_type=memory_type,
                metadata={
                    "message_count": len(messages),
                    "timestamp": datetime.utcnow().isoformat(),
                    "importance_score": importance_score,
                    "context_tags": await self._extract_context_tags(memory_text),
                },
            )

            # Store in database
            await self.db.execute(
                """
                INSERT INTO memories (channel_id, content, embedding, memory_type, metadata)
                VALUES (:channel_id, :content, :embedding, :memory_type, :metadata)
                """,
                {
                    "channel_id": memory.channel_id,
                    "content": memory.content,
                    "embedding": memory.embedding,
                    "memory_type": memory.memory_type,
                    "metadata": memory.metadata,
                },
            )

            # Clear buffer and update last processed time
            self.memory_buffer[channel_id] = []
            self.last_processed[channel_id] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error processing memories: {e}", exc_info=True)

    async def search_memories(
        self,
        channel_id: str,
        query: str,
        limit: int = 5,
        min_importance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories using vector similarity."""
        try:
            # Get embedding for the query
            query_embedding = await self._get_embedding(query)

            # SQL query using vector similarity
            query = """
            SELECT content, metadata, embedding <=> $1 as distance
            FROM memories
            WHERE channel_id = $2
            AND metadata->>'importance_score' >= $3
            ORDER BY embedding <=> $1
            LIMIT $4
            """

            # Execute query with parameters
            results = await self.db.execute_query(
                query, query_embedding, channel_id, str(min_importance), limit
            )

            # Format results
            memories = []
            async for row in results:
                memories.append(
                    {
                        "content": row["content"],
                        "metadata": row["metadata"],
                        "distance": row["distance"],
                    }
                )

            return memories

        except Exception as e:
            logger.error(f"Error searching memories: {e}", exc_info=True)
            return []

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using the embeddings service."""
        try:
            embedding_provider = await self.bot.get_service("ai.embeddings")
            if not embedding_provider:
                raise ValueError("Embeddings service not available")
            return await embedding_provider.get_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
