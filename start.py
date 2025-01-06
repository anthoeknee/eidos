import asyncio
import logging
from src.bot import Bot
from src.loaders import load_all
from src.config import get_config


async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create bot instance
    bot = Bot()

    try:
        # Load services and cogs
        logger.info("Loading services and cogs...")
        services, loaded_cogs = await load_all(bot)
        logger.info(f"Loaded services: {list(services.keys())}")
        logger.info(f"Loaded cogs: {loaded_cogs}")

        # Start the bot
        config = get_config()
        await bot.start(config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
