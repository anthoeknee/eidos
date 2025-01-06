import logging
import os
import glob
import importlib
from typing import Dict, Any, List, Tuple
from src.services.cache import setup as cache_setup
from src.services.database import setup as db_setup
from src.services.ai import setup as ai_setup

logger = logging.getLogger(__name__)


async def load_services(bot) -> Dict[str, Any]:
    """Load all services."""
    logger.info("Attempting to load services: cache, database, ai")

    # Initialize services dictionary if it doesn't exist
    if not hasattr(bot, "services"):
        bot.services = {}

    try:
        # Load cache first
        logger.info("Loading cache service...")
        cache_service = await cache_setup(bot)
        bot.services["cache"] = cache_service

        # Load database next
        logger.info("Loading database service...")
        db_service = await db_setup(bot)
        bot.services["database"] = db_service

        # Load AI service last (since it depends on the others)
        logger.info("Loading AI service...")
        ai_service = await ai_setup(bot)

        # Verify services were loaded
        if not bot.services.get("cache"):
            raise RuntimeError("Cache service failed to register")
        if not bot.services.get("database"):
            raise RuntimeError("Database service failed to register")
        if not bot.services.get("ai"):
            raise RuntimeError("AI service failed to register")

        logger.info(
            f"Successfully loaded services. Available services: {list(bot.services.keys())}"
        )
        return bot.services

    except Exception as e:
        logger.error(f"Error loading services: {str(e)}", exc_info=True)
        raise


async def load_cogs(bot) -> List[str]:
    """Loads all cogs from the cogs directory."""
    cog_dir = os.path.join(os.path.dirname(__file__), "cogs")
    loaded_cogs = []
    for filename in glob.glob(os.path.join(cog_dir, "*.py")):
        if filename.endswith("__init__.py"):
            continue
        module_name = os.path.splitext(os.path.basename(filename))[0]
        try:
            module = importlib.import_module(f"src.cogs.{module_name}")
            if hasattr(module, "setup"):
                await module.setup(bot)
                loaded_cogs.append(module_name)
                logger.info(f"Loaded cog: {module_name}")
            else:
                logger.warning(f"Cog {module_name} has no setup function.")
        except Exception as e:
            logger.error(f"Failed to load cog {module_name}: {e}")
    return loaded_cogs


async def load_all(bot) -> Tuple[Dict[str, object], List[str]]:
    """Loads all services and cogs."""
    services = await load_services(bot)
    cogs = await load_cogs(bot)
    return services, cogs
