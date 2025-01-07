from typing import Optional
from src.services.ai.providers import GoogleAIProvider, CohereAIProvider
from src.services.ai.memory.long_term import LongTermMemory
from src.services.ai.memory.short_term import ShortTermMemory
from src.config import get_config
from src.utils.logger import logger


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


async def setup(bot):
    """Setup function for the AI service."""
    ai_service = AIService(bot)

    try:
        # Initialize core services
        await ai_service.initialize()
        db_service = await bot.get_service("database")
        cache_service = await bot.get_service("cache")

        # Initialize memory systems and register services
        ai_service.short_term_memory = ShortTermMemory(cache_service)
        ai_service.long_term_memory = LongTermMemory(db_service, bot)

        # Register all AI-related services
        services_to_register = {
            "ai": ai_service,
            "ai.long_term_memory": ai_service.long_term_memory,
            "ai.short_term_memory": ai_service.short_term_memory,
        }

        if ai_service.google_ai:
            services_to_register["ai.google"] = ai_service.google_ai
        if ai_service.cohere:
            services_to_register["ai.cohere"] = ai_service.cohere
            services_to_register["ai.embeddings"] = ai_service.cohere

        for name, service in services_to_register.items():
            bot.services[name] = service

        logger.info("🤖 AI Service initialized")
        return ai_service

    except Exception as e:
        logger.error(f"❌ AI Service initialization failed: {str(e)}", exc_info=True)
        raise
