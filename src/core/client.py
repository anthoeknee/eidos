import discord
from discord.ext import commands
from typing import Optional

from src.services.manager import ServiceManager
from src.services.llm.events import LLMEvents
from src.utils import logger

log = logger.setup_logger("eidos_client")


class EidosBot(commands.Bot):
    """Main bot client that integrates all services."""

    def __init__(self, settings):
        """Initialize the bot client.

        Args:
            settings: Application settings
        """
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True

        super().__init__(
            command_prefix=settings.discord.command_prefix,
            intents=intents,
            help_command=None,  # We'll implement our own help command
        )

        self.settings = settings
        self.service_manager: Optional[ServiceManager] = None

    async def setup_hook(self) -> None:
        """Set up bot services and events."""
        try:
            # Initialize Service Manager
            self.service_manager = ServiceManager(self.settings)
            await self.service_manager.initialize()

            # Set up LLM events using the create factory method
            self.llm_events = await LLMEvents.create(self, self.service_manager)

            log.info("Bot services initialized successfully")

        except Exception as e:
            log.error(f"Failed to initialize bot services: {e}")
            raise

    async def close(self) -> None:
        """Clean up resources before shutting down."""
        if self.service_manager:
            await self.service_manager.cleanup()
        await super().close()

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        log.info(f"Logged in as {self.user.name} ({self.user.id})")

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Global error handler for all events.

        Args:
            event: Name of the event that raised the error
        """
        log.error(f"Error in {event}", exc_info=True)
