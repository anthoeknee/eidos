import asyncio
from src.core.bot import NexusBot
from src.core.config import settings
from src.services.storage import init_storage
from src.utils.logger import Logger
from src.services.storage.valkey import ValkeyService
from src.services.storage.eventbus import EventBusService

# Create logger with debug level temporarily to see all messages
logger = Logger(name="Main", level="INFO")


async def main():
    """Main entry point for the bot."""
    try:
        logger = Logger(name="Bot", level="INFO")
        logger.info("Initializing bot...")

        # Initialize storage services
        try:
            async with asyncio.timeout(10):
                await init_storage()
        except asyncio.TimeoutError:
            logger.error("Storage initialization timed out")
            raise
        except Exception as e:
            logger.error(f"Storage initialization failed: {e}")
            raise

        # Create and run bot
        bot = NexusBot()
        bot.service_manager.register("valkey", ValkeyService)
        bot.service_manager.register("event_bus", EventBusService)

        async with bot:
            await bot.start(settings.discord_token)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
