from typing import Dict, List, Optional
from collections import deque
import discord
from src.services.cache import CacheService
from src.config import config


class ShortTermMemory:
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.memory: Dict[int, deque] = {}  # Channel ID -> deque of messages
        self.max_messages = 30
        self.conversation_ttl = config.REDIS_CONVERSATION_TTL

    async def add_message(self, message: discord.Message):
        channel_id = str(message.channel.id)  # Convert to string for consistency
        if channel_id not in self.memory:
            self.memory[channel_id] = deque(maxlen=self.max_messages)

        # Format message with role
        formatted_message = f"{'Bot: ' if message.author.bot else f'{message.author.name}: '}{message.content}"
        self.memory[channel_id].append(formatted_message)

        # Store in cache for persistence
        await self._update_cache(channel_id)

    async def get_messages(self, channel_id: int) -> List[str]:
        if channel_id in self.memory:
            return list(self.memory[channel_id])
        else:
            # Check cache for existing memory
            cached_messages = await self._load_from_cache(channel_id)
            if cached_messages:
                return cached_messages
            return []

    async def _update_cache(self, channel_id: int):
        """Updates the cache with the current memory for a channel."""
        messages = list(self.memory[channel_id])
        await self.cache_service.set(
            f"short_term_memory:{channel_id}",
            str(messages),
            expiry=self.conversation_ttl,
        )

    async def _load_from_cache(self, channel_id: int) -> Optional[List[str]]:
        """Loads memory from cache if available."""
        cached_data = await self.cache_service.get(f"short_term_memory:{channel_id}")
        if cached_data:
            try:
                # Safely evaluate the string as a list
                return eval(cached_data)
            except Exception:
                return None
        return None

    async def clear_channel_memory(self, channel_id: int):
        """Clears the short-term memory for a specific channel."""
        if channel_id in self.memory:
            del self.memory[channel_id]
        await self.cache_service.delete(f"short_term_memory:{channel_id}")

    async def get_metadata(self, channel_id: str):
        """Get conversation metadata for a channel"""
        # Default metadata if none exists
        return {"total_messages": 0, "last_message_time": None, "participants": set()}


async def setup(bot):
    cache_service = await bot.get_service("cache")
    short_term_memory = ShortTermMemory(cache_service)
    return short_term_memory
