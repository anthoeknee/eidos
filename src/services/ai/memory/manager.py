from typing import Optional, List, Dict, Union, Any
from src.services.ai.memory.short_term import ConversationHistory
from src.utils.logger import Logger


class MemoryManager:
    def __init__(self):
        self.conversation_history = ConversationHistory()
        self.logger = Logger(name="MemoryManager", level="INFO")

    async def add_interaction(
        self,
        channel_id: str,
        user_id: str,
        user_message: List[Union[str, Dict[str, Any]]],
        user_content_types: List[str],
        bot_response: List[Union[str, Dict[str, Any]]],
        bot_content_types: List[str],
    ) -> None:
        """
        Add a complete multimodal interaction to history

        Example:
            user_message = ["Hello!", {"url": "image.jpg", "metadata": {"type": "photo"}}]
            user_content_types = ["text", "image"]
            bot_response = ["Here's what I see in your image:", {"url": "processed.jpg"}]
            bot_content_types = ["text", "image"]
        """
        try:
            # Add user message
            await self.conversation_history.add_message(
                channel_id=channel_id,
                user_id=user_id,
                content=user_message,
                content_types=user_content_types,
                is_bot=False,
            )

            # Add bot response
            await self.conversation_history.add_message(
                channel_id=channel_id,
                user_id="BOT",
                content=bot_response,
                content_types=bot_content_types,
                is_bot=True,
            )

        except Exception as e:
            self.logger.error(f"Error adding multimodal interaction to memory: {e}")
            raise

    async def get_conversation_context(self, channel_id: str) -> List[Dict]:
        """Get the conversation history for a channel"""
        try:
            return await self.conversation_history.get_history(channel_id)
        except Exception as e:
            self.logger.error(f"Error retrieving conversation context: {e}")
            return []

    async def clear_conversation(self, channel_id: str) -> None:
        """Clear the conversation history for a channel"""
        try:
            await self.conversation_history.clear_history(channel_id)
        except Exception as e:
            self.logger.error(f"Error clearing conversation: {e}")
            raise
