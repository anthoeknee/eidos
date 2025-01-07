from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy import text
from dataclasses import dataclass
from src.services.database.queries.context_tag import get_or_create_tags
import json
from src.services.ai.memory.nlp import NLP
from src.services.ai.providers import CohereAIProvider
from src.config import get_config

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
    def __init__(self, db_service, bot):
        self.db = db_service
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
        self.nlp = NLP()
        self.processing_task = None
        self.config = get_config()
        self.embeddings = CohereAIProvider(self.config.COHERE_API_KEY)

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
            embeddings = await self.embeddings.get_embedding(
                content=memory_text, content_type="text"
            )

            if not embeddings:
                logger.error(f"Failed to generate embeddings for channel {channel_id}")
                return

            importance_score = await self._analyze_importance(memory_text)
            memory_type = "important" if importance_score > 0.8 else "conversation"

            embedding_array = f"{{{','.join(str(x) for x in embeddings)}}}"

            memory = Memory(
                channel_id=channel_id,
                content=memory_text,
                embedding=embeddings,
                memory_type=memory_type,
                metadata={
                    "message_count": len(messages),
                    "timestamp": datetime.utcnow().isoformat(),
                    "importance_score": importance_score,
                    "context_tags": await self._extract_context_tags(memory_text),
                },
            )

            # Updated column name in the INSERT statement
            with self.db.session() as session:
                session.execute(
                    text("""
                    INSERT INTO memories (channel_id, content, embedding, memory_type, meta_data)
                    VALUES (:channel_id, :content, :embedding::vector, :memory_type, :meta_data::jsonb)
                    """),
                    {
                        "channel_id": memory.channel_id,
                        "content": memory.content,
                        "embedding": embedding_array,
                        "memory_type": memory.memory_type,
                        "meta_data": json.dumps(
                            memory.metadata
                        ),  # Note: we pass as metadata but column is meta_data
                    },
                )
                session.commit()

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
            query_embedding = await self.embeddings.get_embedding(
                content=query, content_type="text"
            )
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []

            embedding_array = f"[{','.join(str(x) for x in query_embedding)}]"

            with self.db.session() as session:
                stmt = text("""
                    SELECT
                        content,
                        meta_data,
                        1 - (embedding <-> :embedding) as similarity
                    FROM memories
                    WHERE channel_id = :channel_id
                    AND (meta_data->>'importance_score')::float >= :importance
                    ORDER BY embedding <-> :embedding
                    LIMIT :limit_val
                """)

                result = session.execute(
                    stmt,
                    {
                        "embedding": embedding_array,
                        "channel_id": channel_id,
                        "importance": min_importance,
                        "limit_val": limit,
                    },
                )

                memories = []
                for row in result:
                    metadata = json.loads(row.meta_data) if row.meta_data else {}
                    memories.append(
                        {
                            "content": row.content,
                            "metadata": metadata,
                            "similarity": float(row.similarity),
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

    async def _analyze_importance(self, memory_text: str) -> float:
        """Analyze the importance of a memory using the NLP service."""
        try:
            return await self.nlp.analyze_importance(memory_text)
        except Exception as e:
            logger.error(f"Error analyzing importance: {e}")
            return 0.0  # Default to low importance on error

    async def _extract_context_tags(self, memory_text: str) -> List[str]:
        """Extract context tags from the memory text using the NLP service."""
        try:
            tags = await self.nlp.extract_context_tags(memory_text)
            await self._store_context_tags(tags)
            return tags
        except Exception as e:
            logger.error(f"Error extracting or storing context tags: {e}")
            return []

    async def _store_context_tags(self, tags: List[str]):
        """Store the extracted context tags in the database."""
        try:
            with self.db.session() as session:
                # Use the new get_or_create_tags function
                get_or_create_tags(session, tags)
                # No need to commit here, as get_or_create_tags handles it

        except Exception as e:
            logger.error(f"Error storing context tags in database: {e}")
            raise

    async def store_image_memory(
        self,
        channel_id: str,
        image_url: str,
        description: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Store an image-related memory."""
        try:
            # Generate embedding for the image description
            embedding = await self.embeddings.get_embedding(
                content=description, content_type="text"
            )

            if not embedding:
                logger.error("Failed to generate embedding for image memory")
                return False

            # Format embedding array for PostgreSQL
            embedding_array = f"{{{','.join(str(x) for x in embedding)}}}"

            # Prepare metadata
            full_metadata = {
                "image_url": image_url,
                "timestamp": datetime.utcnow().isoformat(),
                "importance_score": 0.7,  # Default importance for images
                **(metadata or {}),
            }

            # Store in database
            with self.db.session() as session:
                session.execute(
                    text("""
                    INSERT INTO memories (channel_id, content, embedding, memory_type, metadata)
                    VALUES (:channel_id, :content, :embedding::vector, :memory_type, :metadata::jsonb)
                    """),
                    {
                        "channel_id": channel_id,
                        "content": description,
                        "embedding": embedding_array,
                        "memory_type": "image",
                        "metadata": json.dumps(full_metadata),
                    },
                )
                session.commit()
                return True

        except Exception as e:
            logger.error(f"Error storing image memory: {e}", exc_info=True)
            return False
