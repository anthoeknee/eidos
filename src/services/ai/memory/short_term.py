from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime
import json

from src.services.storage import get_valkey
from src.utils.logger import Logger


@dataclass
class MultimodalContent:
    type: str  # 'text', 'image', 'audio', 'video'
    content: Union[str, Dict[str, Any]]  # Raw content or metadata
    url: Optional[str] = None  # URL for media content if applicable

    def to_dict(self) -> Dict:
        return {"type": self.type, "content": self.content, "url": self.url}

    @classmethod
    def from_dict(cls, data: Dict) -> "MultimodalContent":
        return cls(**data)


@dataclass
class Message:
    user_id: str
    content: List[MultimodalContent]  # Now supports multiple content types per message
    timestamp: float
    is_bot: bool
    channel_id: str

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "content": [c.to_dict() for c in self.content],
            "timestamp": self.timestamp,
            "is_bot": self.is_bot,
            "channel_id": self.channel_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        content = [MultimodalContent.from_dict(c) for c in data["content"]]
        return cls(
            user_id=data["user_id"],
            content=content,
            timestamp=data["timestamp"],
            is_bot=data["is_bot"],
            channel_id=data["channel_id"],
        )


class ConversationHistory:
    def __init__(self, max_messages: int = 10, ttl: int = 3600):
        self.max_messages = max_messages
        self.ttl = ttl  # Time to live in seconds (1 hour default)
        self.logger = Logger(name="ConversationHistory", level="INFO")
        self._valkey = get_valkey()

    def _get_key(self, channel_id: str) -> str:
        """Generate Redis key for a conversation"""
        return f"conversation:{channel_id}"

    async def add_message(
        self,
        channel_id: str,
        user_id: str,
        content: List[Union[str, Dict[str, Any]]],
        content_types: List[str],
        is_bot: bool = False,
    ) -> None:
        """
        Add a multimodal message to the conversation history

        Args:
            channel_id: The channel identifier
            user_id: The user identifier
            content: List of content items (text strings or metadata dicts)
            content_types: List of content types matching the content list
            is_bot: Whether the message is from the bot
        """
        key = self._get_key(channel_id)

        # Convert content to MultimodalContent objects
        multimodal_content = []
        for c, c_type in zip(content, content_types):
            if isinstance(c, str):
                mc = MultimodalContent(type=c_type, content=c)
            else:
                mc = MultimodalContent(
                    type=c_type, content=c.get("metadata", {}), url=c.get("url")
                )
            multimodal_content.append(mc)

        message = Message(
            user_id=user_id,
            content=multimodal_content,
            timestamp=datetime.now().timestamp(),
            is_bot=is_bot,
            channel_id=channel_id,
        )

        try:
            messages = await self.get_history(channel_id)
            messages.append(message.to_dict())
            if len(messages) > self.max_messages:
                messages = messages[-self.max_messages :]
            await self._valkey.set(key, json.dumps(messages), ttl=self.ttl)

        except Exception as e:
            self.logger.error(f"Error adding multimodal message to history: {e}")
            raise

    async def get_history(self, channel_id: str) -> List[Dict]:
        """Get conversation history for a channel"""
        key = self._get_key(channel_id)

        try:
            data = await self._valkey.get(key)
            if data:
                return json.loads(data)
            return []

        except Exception as e:
            self.logger.error(f"Error retrieving conversation history: {e}")
            return []

    async def clear_history(self, channel_id: str) -> None:
        """Clear conversation history for a channel"""
        key = self._get_key(channel_id)
        try:
            await self._valkey.delete(key)
        except Exception as e:
            self.logger.error(f"Error clearing conversation history: {e}")
            raise
