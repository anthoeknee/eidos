import discord
from discord.ext import commands
import logging
import traceback

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,  # This will make the bot only respond to mentions
            intents=discord.Intents.all(),  # Enable all intents
            help_command=None,  # Disable the default help command
        )
        self.config = None  # Will be set during initialization

        self.services = {}

    async def get_service(self, service_name: str):
        """Get a service by name."""
        service = self.services.get(service_name)
        if not service:
            logger.warning(f"Service '{service_name}' not found")
        return service

    async def get_all_services(self):
        """Get a list of all registered services."""
        return list(self.services.keys())

    async def setup_hook(self):
        """This is called when the bot is starting up."""
        logger.info("Bot is starting up...")

        # Remove the manual cog loading since it's handled by loaders.py
        # print("Loading chat cog...")
        # try:
        #     await self.load_extension("src.cogs.chat")
        #     print("Chat cog loaded successfully")
        # except Exception as e:
        #     print(f"Error loading chat cog: {e}")
        #     traceback.print_exc()

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
