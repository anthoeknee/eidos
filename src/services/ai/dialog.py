from typing import List, Dict, Any, Union
from src.services.ai.memory import get_memory_manager
from src.services.ai.providers.google import GoogleAIProvider
from src.core.config import settings
from src.utils.logger import Logger
from src.services.base import BaseService


class DialogService(BaseService):
    def __init__(self):
        super().__init__()
        self.memory_manager = get_memory_manager()
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
            history = await self.memory_manager.get_conversation_context(channel_id)

            # Format the prompt for the AI model
            prompt = self._format_prompt(history, user_message)

            # Generate response from AI model
            response_text = await self.ai_provider.generate_content(prompt)

            # Format the response
            bot_response = [response_text]
            bot_content_types = ["text"]

            # Add interaction to memory
            await self.memory_manager.add_interaction(
                channel_id=channel_id,
                user_id=user_id,
                user_message=user_message,
                user_content_types=user_content_types,
                bot_response=bot_response,
                bot_content_types=bot_content_types,
            )

            return bot_response

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return ["I encountered an error processing your request."]

    def _format_prompt(
        self, history: List[Dict], user_message: List[Union[str, Dict[str, Any]]]
    ) -> str:
        """
        Formats the prompt for the AI model.

        Args:
            history: The conversation history.
            user_message: The user's message.

        Returns:
            The formatted prompt string.
        """
        prompt = "Conversation History:\n"
        for message in history:
            if message["is_bot"]:
                prompt += f"Bot: {message['content']}\n"
            else:
                prompt += f"User: {message['content']}\n"

        prompt += f"User: {user_message}\n"
        prompt += "Bot:"
        return prompt

    async def start(self) -> None:
        """Start the service."""
        self.logger.info("Dialog service started.")

    async def stop(self) -> None:
        """Stop the service."""
        self.logger.info("Dialog service stopped.")

    async def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return True
