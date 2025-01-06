from typing import Optional
from src.services.ai.providers import GoogleAIProvider, CohereAIProvider
from src.services.ai.memory.long_term import LongTermMemory
from src.services.ai.memory.short_term import ShortTermMemory
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, bot):
        self.bot = bot
        self.google_ai: Optional[GoogleAIProvider] = None
        self.cohere: Optional[CohereAIProvider] = None
        self.long_term_memory: Optional[LongTermMemory] = None
        self.short_term_memory: Optional[ShortTermMemory] = None
        self.config = get_config()

    async def initialize(self):
        """Initialize AI providers with their respective API keys."""
        if self.config.GOOGLE_API_KEY:
            self.google_ai = GoogleAIProvider(api_key=self.config.GOOGLE_API_KEY)

        if self.config.COHERE_API_KEY:
            self.cohere = CohereAIProvider(api_key=self.config.COHERE_API_KEY)

        # Initialize memory systems
        self.long_term_memory = LongTermMemory(self.bot)
        self.short_term_memory = ShortTermMemory()


async def setup(bot):
    """Setup function for the AI service."""
    logger.info("Initializing AI service...")

    ai_service = AIService(bot)
    await ai_service.initialize()

    # Get required services
    logger.info("Fetching required services...")
    db_service = await bot.get_service("database")
    cache_service = await bot.get_service("cache")

    # Initialize memory systems
    logger.info("Initializing memory systems...")
    ai_service.short_term_memory = ShortTermMemory(cache_service)
    ai_service.long_term_memory = LongTermMemory(db_service, ai_service.cohere)

    # Register services with explicit logging
    logger.info("Registering AI services...")
    bot.services["ai.long_term_memory"] = ai_service.long_term_memory
    bot.services["ai.short_term_memory"] = ai_service.short_term_memory
    if ai_service.google_ai:
        bot.services["ai.google"] = ai_service.google_ai
    if ai_service.cohere:
        bot.services["ai.cohere"] = ai_service.cohere
    bot.services["ai"] = ai_service

    # Log available services
    logger.info(f"Available services after registration: {list(bot.services.keys())}")

    return ai_service
