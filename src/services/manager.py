from typing import Optional
from src.services.llm.core import LLMService
from src.utils import logger

log = logger.setup_logger("service_manager")


class ServiceManager:
    """Manages all bot services."""

    def __init__(self, settings):
        """Initialize service manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.llm = LLMService(settings)

    async def initialize(self) -> None:
        """Initialize all services."""
        try:
            # Initialize LLM service first
            await self.llm.initialize()

            log.info("Service manager initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize services: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup all services."""
        if self.llm:
            await self.llm.cleanup()
