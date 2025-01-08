import asyncio
from src.bot import Bot
from src.loaders import load_all
from src.config import get_config
from src.utils.logger import logger
import discord


async def main():
    # Create bot instance
    bot = Bot()

    try:
        await load_all(bot)

        # Start the bot
        config = get_config()
        while True:
            try:
                await bot.start(config.DISCORD_TOKEN)
            except discord.errors.ConnectionClosed as e:
                logger.warning(
                    f"WebSocket connection closed: {e}. Attempting to reconnect..."
                )
                await asyncio.sleep(5)  # Wait before attempting to reconnect
            except Exception as e:
                logger.error(f"Error during startup: {e}", exc_info=True)
                raise
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
