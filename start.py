import asyncio
from src.core.bot import EidosBot
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(log_level=settings.log_level)


async def main():
    """Main function to initialize and start the bot."""
    bot = EidosBot()
    try:
        await bot.start(settings.discord_token)
    except Exception as e:
        logger.critical(f"Failed to start the bot: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
