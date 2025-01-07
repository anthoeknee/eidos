import asyncio
from src.bot import Bot
from src.loaders import load_all
from src.config import get_config
from src.utils.logger import logger


async def main():
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
        logger.error(f"Error during startup: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
