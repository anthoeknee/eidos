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
        logger.debug("Starting main function")

        # Initialize storage services with more detailed logging
        logger.info("Initializing storage...")
        try:
            async with asyncio.timeout(10):  # 10 second timeout
                await init_storage()
        except asyncio.TimeoutError:
            logger.error("Storage initialization timed out after 10 seconds")
            raise
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            logger.exception(e)
            raise

        # Create and run bot
        logger.info("Creating bot instance...")
        bot = NexusBot()

        # Register storage services with the bot's service manager
        bot.service_manager.register("valkey", ValkeyService)
        bot.service_manager.register("event_bus", EventBusService)

        logger.info("Bot instance created, connecting to Discord...")

        async with bot:
            logger.info("Starting bot with token...")
            await bot.start(settings.discord_token)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception(e)
        raise


if __name__ == "__main__":
    asyncio.run(main())
