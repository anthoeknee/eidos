from typing import Dict, List, Optional
from collections import deque
import discord
from src.services.cache import CacheService
from src.config import config
import json


class ShortTermMemory:
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.memory: Dict[str, deque] = {}  # Channel ID -> deque of messages
        self.max_messages = 30
        self.conversation_ttl = config.REDIS_CONVERSATION_TTL

    async def add_message(self, message: discord.Message):
        channel_id = str(message.channel.id)
        if channel_id not in self.memory:
            self.memory[channel_id] = deque(maxlen=self.max_messages)

        formatted_message = {
            "author_id": str(message.author.id),
            "author_name": message.author.name,
            "message_id": str(message.id),
            "timestamp": message.created_at.isoformat(),
            "content": message.content,
            "is_bot": message.author.bot,
        }
        self.memory[channel_id].append(formatted_message)

        await self._update_cache(channel_id)

    async def get_messages(self, channel_id: str) -> List[str]:
        if channel_id in self.memory:
            formatted_messages = []
            for msg in self.memory[channel_id]:
                if msg.get("is_bot"):
                    formatted_messages.append(f"Bot: {msg.get('content')}")
                else:
                    formatted_messages.append(
                        f"{msg.get('author_name')}: {msg.get('content')}"
                    )
            return formatted_messages
        else:
            cached_messages = await self._load_from_cache(channel_id)
            if cached_messages:
                formatted_messages = []
                for msg in cached_messages:
                    if msg.get("is_bot"):
                        formatted_messages.append(f"Bot: {msg.get('content')}")
                    else:
                        formatted_messages.append(
                            f"{msg.get('author_name')}: {msg.get('content')}"
                        )
                return formatted_messages
            return []

    async def _update_cache(self, channel_id: str):
        messages = list(self.memory[channel_id])
        await self.cache_service.set(
            f"short_term_memory:{channel_id}",
            json.dumps(messages),
            expiry=self.conversation_ttl,
        )

    async def _load_from_cache(self, channel_id: str) -> Optional[List[Dict]]:
        cached_data = await self.cache_service.get(f"short_term_memory:{channel_id}")
        if cached_data:
            try:
                return json.loads(cached_data)
            except Exception:
                return None
        return None

    async def clear_channel_memory(self, channel_id: str):
        if channel_id in self.memory:
            del self.memory[channel_id]
        await self.cache_service.delete(f"short_term_memory:{channel_id}")

    async def get_metadata(self, channel_id: str) -> Dict:
        if channel_id in self.memory:
            messages = list(self.memory[channel_id])
            participants = set(msg["author_name"] for msg in messages)
            last_message_time = (
                messages[-1]["timestamp"] if messages else None
            )  # Get the timestamp of the last message
            return {
                "total_messages": len(messages),
                "last_message_time": last_message_time,
                "participants": list(participants),
            }
        else:
            return {
                "total_messages": 0,
                "last_message_time": None,
                "participants": [],
            }


async def setup(bot):
    cache_service = await bot.get_service("cache")
    short_term_memory = ShortTermMemory(cache_service)
    return short_term_memory
