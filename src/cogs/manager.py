from pathlib import Path
from typing import List, Optional, Dict, Any
import importlib.util
import sys
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)


class CogManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cogs_path = Path(__file__).parent
        self.loaded_cogs: Dict[str, Any] = {}

    async def load_all_cogs(self) -> None:
        """Recursively load all cogs from the cogs directory."""
        for item in self.cogs_path.rglob("*.py"):
            if item.name.startswith("_"):
                continue

            if item.name in ["base.py", "manager.py"]:
                continue

            try:
                await self._load_cog(item)
            except Exception as e:
                logger.error(f"Failed to load cog {item}: {str(e)}")

    async def _load_cog(self, path: Path) -> None:
        """Load a single cog from file path."""
        # Convert path to module path
        relative_path = path.relative_to(Path(__file__).parent.parent)
        module_path = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

        # Import the module
        spec = importlib.util.spec_from_file_location(module_path, str(path))
        if not spec or not spec.loader:
            raise ImportError(f"Could not load spec for {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_path] = module
        spec.loader.exec_module(module)

        # Find and load the cog
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and hasattr(attr, "__cog_commands__"):
                cog = attr(self.bot)
                await self.bot.add_cog(cog)
                self.loaded_cogs[attr_name] = cog
                logger.info(f"Loaded cog: {attr_name}")
                break

    async def reload_cog(self, cog_name: str) -> bool:
        """Reload a specific cog."""
        try:
            await self.bot.reload_extension(f"cogs.{cog_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload cog {cog_name}: {str(e)}")
            return False
