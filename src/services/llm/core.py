import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from PIL import Image
from google.genai import types
from google import genai
import aiohttp

from src.services.base import BaseService
from src.services.llm.memory.short_term import Message, ShortTermMemory
from src.utils import logger
from .personality import PersonalityManager

log = logger.setup_logger(__name__)


class LLMService(BaseService):
    """Core LLM service that manages the provider, memory, and caching."""

    def __init__(self, settings, personality_manager=None):
        """Initialize the LLM service.

        Args:
            settings: Application settings
            personality_manager: Personality manager (optional)
        """
        super().__init__()
        # Initialize the client with just the API key string
        self.client = genai.Client(api_key=settings.ai.google_api_key)
        self.personality = personality_manager or PersonalityManager()
        # Remove model initialization and just store model name
        self.model_name = "gemini-2.0-flash-exp"
        self.chats = {}  # Store active chat sessions
        # Add short-term memory
        self.memory = ShortTermMemory(max_messages=35, ttl_minutes=45)

    async def initialize(self) -> None:
        """Initialize the LLM service."""
        logging.info("Initializing LLM service with Gemini")

    def _get_or_create_chat(self, channel_id: str, system_prompt: str = None) -> Any:
        """Get existing chat or create new one for the channel."""
        if channel_id not in self.chats:
            config = types.GenerateContentConfig(
                temperature=0.7,
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_ONLY_HIGH",
                    )
                ],
            )

            self.chats[channel_id] = self.client.chats.create(
                model=self.model_name, config=config
            )

            if system_prompt:
                self.chats[channel_id].send_message(system_prompt)

        return self.chats[channel_id]

    async def process_message(
        self,
        content: str,
        author_id: str,
        channel_id: str,
        attachments: List[Dict[str, Any]] = None,
        mentions: List[Dict] = None,
        user_info: Dict[str, str] = None,
        bot_info: Dict[str, str] = None,
        channel_info: Dict[str, str] = None,
    ) -> Optional[str]:
        """Process a message with potential attachments."""
        try:
            # Check if we need to populate context
            if (
                len(self.memory.get_channel_context(channel_id))
                < self.memory.max_messages // 2
            ):
                # We'll need to pass this from events.py
                if channel_info.get("discord_channel"):
                    await self.memory.populate_context(channel_info["discord_channel"])

            # Store message in memory with timezone-aware datetime
            message = Message(
                content=content,
                author_id=author_id,
                timestamp=datetime.now(timezone.utc),  # Make timestamp timezone-aware
                channel_id=channel_id,
                attachments=attachments or [],
                mentions=mentions or [],
                is_bot=False,
            )
            self.memory.add_message(message)

            # Get recent context from memory
            recent_messages = self.memory.get_channel_context(channel_id, limit=5)
            context_text = self._format_context(recent_messages)

            # Generate personality-aware system prompt
            system_prompt = self.personality.get_prompt(
                {
                    "channel_type": "dm" if not channel_id.isdigit() else "text",
                    "user_info": user_info,
                    "bot_info": bot_info,
                    "channel_info": channel_info,
                }
            )

            # Combine context, system prompt and current message
            full_prompt = f"{system_prompt}\n\nRecent conversation:\n{context_text}\n\nCurrent message: {content}"

            # Process any attachments
            if attachments:
                return await self._process_multimodal(full_prompt, attachments)

            # Text-only response
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_ONLY_HIGH",
                        )
                    ],
                ),
            )

            # Store bot's response in memory with timezone-aware datetime
            bot_message = Message(
                content=response.text,
                author_id=bot_info.get("username", "bot"),
                timestamp=datetime.now(timezone.utc),  # Make timestamp timezone-aware
                channel_id=channel_id,
                attachments=[],
                is_bot=True,
            )
            self.memory.add_message(bot_message)

            return response.text

        except Exception as e:
            logging.error(f"Error in process_message: {str(e)}", exc_info=True)
            return "I encountered an error processing your message."

    def _format_context(self, messages: List[Message]) -> str:
        """Format message history into a string for context."""
        context = []
        for msg in messages:
            author = "Bot" if msg.is_bot else "User"
            # Format the content with proper mention handling
            content = msg.content
            if msg.mentions:
                for mention in msg.mentions:
                    if mention["type"] == "user":
                        content = content.replace(
                            f"<@{mention['id']}>", f"@{mention['name']}"
                        )
                    elif mention["type"] == "role":
                        content = content.replace(
                            f"<@&{mention['id']}>", f"@{mention['name']}"
                        )
                    elif mention["type"] == "channel":
                        content = content.replace(
                            f"<#{mention['id']}>", f"#{mention['name']}"
                        )

            attachments_info = ""
            if msg.attachments:
                att_types = [att.get("content_type", "file") for att in msg.attachments]
                attachments_info = f" (with {', '.join(att_types)})"

            context.append(f"{author}: {content}{attachments_info}")
        return "\n".join(context)

    async def _process_multimodal(
        self, prompt: str, attachments: List[Dict[str, Any]]
    ) -> str:
        """Process a message with attachments."""
        try:
            contents = [prompt]

            for att in attachments:
                if att.get("content_type", "").startswith(("image/", "video/")):
                    # Download and process the attachment
                    async with aiohttp.ClientSession() as session:
                        async with session.get(att["url"]) as response:
                            file_data = await response.read()

                            if att["content_type"].startswith("image/"):
                                image = Image.open(io.BytesIO(file_data))
                                contents.append(image)
                            # Add video processing if needed

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.7),
            )
            return response.text

        except Exception as e:
            logging.error(f"Error processing multimodal content: {e}")
            return "I encountered an error processing the attachments."

    def end_chat(self, channel_id: str):
        """End a chat session for a channel."""
        if channel_id in self.chats:
            del self.chats[channel_id]

    async def cleanup(self) -> None:
        """Cleanup resources when shutting down."""
        try:
            # End all active chat sessions
            for channel_id in list(self.chats.keys()):
                self.end_chat(channel_id)
            self.chats.clear()
            logging.info("LLM service cleanup completed")
        except Exception as e:
            logging.error(f"Error during LLM service cleanup: {str(e)}", exc_info=True)
