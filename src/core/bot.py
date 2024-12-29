import discord
from discord.ext import commands
from src.core.config import settings
from src.services.manager import ServiceManager
from src.utils.logger import Logger
from src.cogs import CogManager


class NexusBot(commands.Bot):
    """
    Main bot class for Nexus Discord Bot.
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=settings.discord_command_prefix,
            intents=intents,
            owner_id=settings.discord_owner_id,
        )

        self.logger = Logger(name="NexusBot", level=settings.log_level)
        self.service_manager = ServiceManager()
        self.cog_manager = CogManager(self)

    async def setup_hook(self):
        """Initialize bot services and load extensions."""
        # Start all services
        await self.service_manager.start_all()

        # Load all cogs
        try:
            await self.cog_manager.load_all_cogs()
            self.logger.info("All cogs loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading cogs: {e}")

    async def close(self):
        """Clean up and close the bot."""
        self.logger.info("Shutting down bot...")
        await self.service_manager.stop_all()
        await super().close()

    async def on_ready(self):
        """Called when the bot is ready."""
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info(f"Connected to {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name=f"{self.command_prefix}help"
            )
        )
