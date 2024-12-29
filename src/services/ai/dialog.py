from typing import List, Dict, Any, Union
from src.services.ai.memory.service import MemoryService
from src.services.ai.providers.google import GoogleAIProvider
from src.core.config import settings
from src.utils.logger import Logger
from src.services.base import BaseService
from src.services.storage.valkey import ValkeyService


class DialogService(BaseService):
    def __init__(self, valkey: ValkeyService):
        super().__init__()
        self.memory_service = MemoryService(valkey=valkey)
        self.ai_provider = GoogleAIProvider(api_key=settings.google_api_key)
        self.logger = Logger(name="DialogService", level="INFO")

    async def generate_response(
        self,
        channel_id: str,
        user_id: str,
        user_message: List[Union[str, Dict[str, Any]]],
        user_content_types: List[str],
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        Generates a response from the AI model based on the conversation history.

        Args:
            channel_id: The channel identifier.
            user_id: The user identifier.
            user_message: The user's message content.
            user_content_types: The content types of the user's message.

        Returns:
            The AI's response content.
        """
        try:
            # Get conversation history
            history = await self.memory_service.get_memories(channel_id)

            # Format the conversation history into a prompt
            formatted_history = []

            # Process historical messages
            for memory in history:
                if isinstance(memory, dict):
                    content = memory.get("content", [])
                    if isinstance(content, list) and content:
                        first_content = content[0]  # Get the first content item

                        # Extract message content
                        if isinstance(first_content, dict):
                            message_text = first_content.get("user_message", [""])[0]
                            response_text = first_content.get("bot_response", [""])[0]

                            if message_text:
                                formatted_history.append(f"Human: {message_text}")
                            if response_text:
                                formatted_history.append(f"Assistant: {response_text}")

            # Add the current message
            current_message = (
                user_message[0]
                if isinstance(user_message[0], str)
                else user_message[0].get("content", "")
            )
            formatted_history.append(f"Human: {current_message}")
            formatted_history.append("Assistant:")

            # Create the final prompt
            prompt = "\n".join(formatted_history)

            # Generate response from AI model
            response_text = await self.ai_provider.generate_content(prompt)

            # Ensure response is properly formatted
            if isinstance(response_text, (list, tuple)):
                response_text = response_text[0]

            # Create a properly formatted response
            bot_response = [str(response_text)]
            bot_content_types = ["text"]

            # Add interaction to memory
            await self.memory_service.create_memory(
                category=channel_id,
                content=[
                    {
                        "user_id": user_id,
                        "user_message": user_message,
                        "user_content_types": user_content_types,
                        "bot_response": bot_response,
                        "bot_content_types": bot_content_types,
                        "is_bot": False,
                    }
                ],
            )
            await self.memory_service.create_memory(
                category=channel_id,
                content=[
                    {
                        "user_id": "BOT",
                        "user_message": bot_response,
                        "user_content_types": bot_content_types,
                        "is_bot": True,
                    }
                ],
            )

            return bot_response

        except Exception as e:
            self.logger.error(f"Error generating response: {e}", exc_info=True)
            return ["I encountered an error processing your request."]

    async def start(self) -> None:
        """Start the service."""
        await self.memory_service.start()
        self.logger.info("Dialog service started.")

    async def stop(self) -> None:
        """Stop the service."""
        await self.memory_service.stop()
        self.logger.info("Dialog service stopped.")

    async def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return True

    async def _get_conversation_context(self, channel_id: str) -> str:
        history = await self.memory_service.get_memories(channel_id)
        self.logger.debug(f"[_get_conversation_context] Raw history: {history}")

        formatted_messages = []
        for message in history:
            self.logger.debug(
                f"[_get_conversation_context] Processing message: {message}"
            )
            if hasattr(message, "content"):
                for content_item in message.content:
                    self.logger.debug(
                        f"[_get_conversation_context] Content item: {content_item}"
                    )
                    if content_item.content and content_item.content[0]:
                        prefix = "Assistant: " if message.is_bot else "Human: "
                        if isinstance(content_item.content[0], str):
                            formatted_messages.append(
                                f"{prefix}{content_item.content[0]}"
                            )
                        elif isinstance(content_item.content[0], dict):
                            # Handle dictionary content (like function calls or structured data)
                            text_content = content_item.content[0].get("text", "")
                            if text_content:
                                formatted_messages.append(f"{prefix}{text_content}")

        self.logger.debug(
            f"[_get_conversation_context] Formatted messages: {formatted_messages}"
        )
        return "\n".join(formatted_messages)

    async def get_response(
        self,
        channel_id: str,
        message_content: List[Union[str, Dict[str, Any]]],
        **kwargs,
    ) -> str:
        try:
            context = await self._get_conversation_context(channel_id)
            self.logger.debug(f"[get_response] Context being sent to AI: {context}")

            # Rest of your get_response implementation...
            # Your existing code here...

        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}", exc_info=True)
            raise
