import discord
from discord.ext import commands
import asyncio
from src.config import config
from src.loaders import load_all
from src.utils import logger


class EidosBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_loader = None
        self.cog_loader = None
        self.db = None
        self.cache = None

    async def setup_hook(self) -> None:
        """Setup hook to load services and cogs."""
        try:
            services, self.cog_loader = await load_all(self)
            logger.info("All services and cogs loaded successfully.")
            await self.setup_services(services)
        except Exception as e:
            logger.critical(f"Failed to load services or cogs: {e}")
            await self.close()

    async def on_ready(self):
        """Event handler when the bot is ready."""
        logger.success(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds.")
        await self.sync_app_commands()

    async def sync_app_commands(self):
        """Sync application commands."""
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} application commands.")
        except Exception as e:
            logger.error(f"Failed to sync application commands: {e}")

    async def on_command_error(self, ctx, error):
        """Global command error handler."""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required arguments.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments provided.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("An error occurred while processing the command.")

    async def setup_services(self, services):
        self.db = services.get("database")
        self.cache = services.get("cache")


async def main():
    """Main function to run the bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = EidosBot(
        command_prefix=config.DISCORD_COMMAND_PREFIX,
        intents=intents,
        owner_id=config.DISCORD_OWNER_ID,
    )

    try:
        await bot.start(config.DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.critical("Discord token is invalid. Please check your .env file.")
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}")


if __name__ == "__main__":
    asyncio.run(main())
