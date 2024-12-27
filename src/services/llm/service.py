from typing import Optional, List, Dict, Any
from src.services.llm.provider import GoogleGeminiProvider
from src.utils import logger

log = logger.setup_logger("llm_service")


class LLMService:
    def __init__(self, settings):
        self.settings = settings
        self.provider = GoogleGeminiProvider(settings)
        self.chats = {}  # Store active chat sessions
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the LLM service and provider."""
        if not self._initialized:
            await self.provider.initialize()
            self._initialized = True

    async def process_message(
        self,
        content: str,
        author_id: str,
        channel_id: str,
        attachments: List[Dict[str, Any]] = None,
        user_info: Dict[str, str] = None,
        bot_info: Dict[str, str] = None,
        channel_info: Dict[str, str] = None,
    ) -> str:
        """Process a message with context."""
        if not self._initialized:
            await self.initialize()

        try:
            # Get chat history for the channel
            history = self.chats.get(channel_id, [])

            # Add the new message to history
            history.append({"role": "user", "content": content, "author_id": author_id})

            # Generate response
            response = await self.provider.chat(
                message=content,
                history=history,
                temperature=0.7,
            )

            # Update chat history with response
            history.append({"role": "assistant", "content": response})

            # Store updated history
            self.chats[channel_id] = history[-10:]  # Keep last 10 messages

            if hasattr(response, "function_call") and response.function_call:
                return await self.events._handle_function_call(response.function_call)

            return response.text

        except Exception as e:
            log.error(f"Error processing message: {e}", exc_info=True)
            return "Sorry, I encountered an error processing your request."

    async def cleanup(self) -> None:
        """Cleanup the service."""
        self._initialized = False
