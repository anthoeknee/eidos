from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List


@dataclass
class Message:
    """Represents a message in the short-term memory."""

    content: str
    author_id: str
    timestamp: datetime
    channel_id: str
    attachments: List[Dict[str, Any]]
    mentions: List[Dict] = None
    is_bot: bool = False

    def __init__(
        self,
        content: str,
        author_id: str,
        timestamp: datetime,
        channel_id: str,
        attachments: List[Dict] = None,
        mentions: List[Dict] = None,
        is_bot: bool = False,
    ):
        self.content = content
        self.author_id = author_id
        self.timestamp = timestamp
        self.channel_id = channel_id
        self.attachments = attachments or []
        self.mentions = mentions or []
        self.is_bot = is_bot


class ShortTermMemory:
    """Manages short-term memory for the bot using a circular buffer with TTL."""

    def __init__(self, max_messages: int = 30, ttl_minutes: int = 45):
        """Initialize short-term memory.

        Args:
            max_messages: Maximum number of messages to store per channel
            ttl_minutes: Time-to-live in minutes for messages
        """
        self.max_messages = max_messages
        self.ttl = timedelta(minutes=ttl_minutes)
        self.channel_messages = {}  # Dict[str, deque[Message]]

    def add_message(self, message: Message) -> None:
        """Add a message to the memory buffer.

        Args:
            message: Message to add
        """
        channel_id = message.channel_id
        if channel_id not in self.channel_messages:
            self.channel_messages[channel_id] = deque(maxlen=self.max_messages)

        self._cleanup_expired(channel_id)
        self.channel_messages[channel_id].append(message)

    def get_channel_context(
        self, channel_id: str, limit: Optional[int] = None
    ) -> List[Message]:
        """Get recent messages from a specific channel.

        Args:
            channel_id: ID of the channel to get messages from
            limit: Optional limit on number of messages to return

        Returns:
            List of recent non-expired messages from the specified channel
        """
        if channel_id not in self.channel_messages:
            return []

        self._cleanup_expired(channel_id)
        messages = list(self.channel_messages[channel_id])
        if limit:
            messages = messages[-limit:]
        return messages

    def _cleanup_expired(self, channel_id: str) -> None:
        """Remove expired messages based on TTL for a specific channel."""
        if channel_id not in self.channel_messages:
            return

        current_time = datetime.now(timezone.utc)
        while (
            self.channel_messages[channel_id]
            and (current_time - self.channel_messages[channel_id][0].timestamp)
            > self.ttl
        ):
            self.channel_messages[channel_id].popleft()

    def clear(self) -> None:
        """Clear all messages from memory."""
        self.channel_messages.clear()

    async def populate_context(self, channel, limit: Optional[int] = None) -> None:
        """Populate the memory buffer with recent messages from the channel.

        Args:
            channel: Discord channel object
            limit: Optional number of messages to fetch (defaults to max_messages)
        """
        if not limit:
            limit = self.max_messages

        try:
            async for message in channel.history(limit=limit):
                # Convert Discord message to our Message format
                msg = Message(
                    content=message.content,
                    author_id=str(message.author.id),
                    timestamp=message.created_at,
                    channel_id=str(message.channel.id),
                    attachments=[
                        {"url": attachment.url, "filename": attachment.filename}
                        for attachment in message.attachments
                    ],
                    is_bot=message.author.bot,
                )
                # Add to memory (this will handle TTL and max messages automatically)
                self.add_message(msg)
        except Exception as e:
            print(f"Error populating context: {e}")

    # Usage example in your bot's message handler:
    """
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        # Ensure context is populated before processing
        if len(memory.get_channel_context(str(message.channel.id))) < memory.max_messages // 2:
            await memory.populate_context(message.channel)

        # Process message...
    """
