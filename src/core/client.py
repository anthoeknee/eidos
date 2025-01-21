# src/core/client.py
import discord
from discord.ext import commands
from src.core.config import settings
from src.utils.logger import logger
from src.core.module_manager import module


@module(
    name="client",
    module_type="core",
    description="Discord bot client",
)
class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=settings.bot_prefix, intents=intents)

    async def setup_hook(self) -> None:
        """Sync commands."""
        try:
            await self.tree.sync()
            logger.info("Slash commands synced.")
        except Exception as e:
            logger.error(f"Error during setup_hook: {e}")
            raise

    async def close(self):
        """Close the bot."""
        logger.info("Closing bot.")
        await super().close()
        logger.info("Bot closed.")

    async def on_ready(self):
        """Log when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message):
        """Process messages."""
        if message.author == self.user:
            return
        self.dispatch("message_process", message)
        await self.process_commands(message)


def create_bot() -> DiscordBot:
    """Create and configure the Discord bot."""
    bot = DiscordBot()
    logger.info("Bot created and configured.")
    return bot
