import os
from typing import List

from src.core.bot import EidosBot
from src.utils.logger import logger


class CogManager:
    """Manages the loading and unloading of cogs."""

    def __init__(self, bot: EidosBot, cogs_dir: str = "src/cogs"):
        self.bot = bot
        self.cogs_dir = cogs_dir
        self.cogs: List[str] = []

    async def load_cogs(self):
        """Loads all cogs from the cogs directory."""
        logger.info("Loading cogs...")
        for module_name in self._discover_cogs():
            try:
                await self.bot.load_extension(module_name)
                self.cogs.append(module_name)
                logger.info(f"Loaded cog: {module_name}")
            except Exception as e:
                logger.error(f"Failed to load cog from {module_name}: {e}")
        logger.info("All cogs loaded.")

    async def unload_cogs(self):
        """Unloads all loaded cogs."""
        logger.info("Unloading cogs...")
        for cog in reversed(self.cogs):
            try:
                await self.bot.unload_extension(cog)
                logger.info(f"Unloaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to unload cog: {e}")
        self.cogs.clear()
        logger.info("All cogs unloaded.")

    def _discover_cogs(self) -> List[str]:
        """Discovers cog modules in the cogs directory."""
        cog_modules = []
        for root, _, files in os.walk(self.cogs_dir):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    module_path = os.path.join(root, file)
                    module_name = (
                        module_path.replace(os.sep, ".")
                        .replace(".py", "")
                        .replace("src.", "")
                    )
                    cog_modules.append(module_name)
        return cog_modules
