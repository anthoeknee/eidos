# start.py
import asyncio
from src.core.client import create_bot
from src.core.module_manager import ModuleManager
from src.utils.logger import logger
from src.core.config import load_config
from pathlib import Path


async def main():
    """Main entry point for the bot."""
    bot = None
    try:
        config = load_config()
        bot = create_bot()
        bot.config = config

        base_dir = Path(__file__).resolve().parent / "src"
        module_manager = ModuleManager(str(base_dir))
        module_manager.set_bot(bot)
        bot.module_manager = module_manager

        # Load modules and initialize the bot
        await module_manager.load_modules()
        await module_manager.initialize_bot()

        logger.info("Loaded modules: %s", module_manager.list_modules())

        await bot.start(config.discord_token)

    except Exception as e:
        logger.error("An error occurred while starting the bot: %s", str(e))
        logger.error("Full error details:", exc_info=True)
        raise

    finally:
        if bot is not None:
            await cleanup(bot)


async def cleanup(bot):
    """Handle graceful shutdown of the bot and all tasks."""
    try:
        if bot.is_ready():
            await bot.close()

        pending = [
            t
            for t in asyncio.all_tasks()
            if t is not asyncio.current_task() and not t.done()
        ]

        for task in pending:
            task.cancel()

        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    except Exception as e:
        logger.error("Error during cleanup: %s", str(e))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown initiated by user")
    except Exception as e:
        logger.error("Fatal error occurred:", exc_info=True)
