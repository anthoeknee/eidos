import asyncio

from src.core.config import settings
from src.core.client import EidosBot
from src.utils import logger

# Set up custom logger
log = logger.setup_logger("eidos_bot")


async def main():
    """Main entry point for the bot."""
    try:
        # Create and start the bot
        bot = EidosBot(settings)
        async with bot:
            log.info("Starting Eidos Bot...")
            await bot.start(settings.discord_token)

    except Exception as e:
        log.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
