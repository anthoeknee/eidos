import logging
import os
import glob
import importlib
from typing import Dict, Any, List, Tuple
from src.services.cache import setup as cache_setup
from src.services.database import setup as db_setup
from src.services.ai import setup as ai_setup
from src.utils.logger import logger


async def load_services(bot) -> Dict[str, Any]:
    """Load all services."""
    try:
        services_to_load = [
            ("cache", cache_setup),
            ("database", db_setup),
            ("ai", ai_setup),
        ]

        for service_name, setup_func in services_to_load:
            bot.services[service_name] = await setup_func(bot)

        # Only show top-level services in the log
        top_level_services = {name.split(".")[0] for name in bot.services.keys()}
        logger.info(
            f"🔌 Core services initialized: {', '.join(sorted(top_level_services))}"
        )
        return bot.services

    except Exception as e:
        logger.error(f"❌ Service loading failed: {str(e)}", exc_info=True)
        raise


async def load_cogs(bot) -> List[str]:
    """Loads all cogs from the cogs directory."""
    cog_dir = os.path.join(os.path.dirname(__file__), "cogs")
    loaded_cogs = []
    failed_cogs = []

    for filename in glob.glob(os.path.join(cog_dir, "*.py")):
        if filename.endswith("__init__.py"):
            continue

        module_name = os.path.splitext(os.path.basename(filename))[0]
        try:
            module = importlib.import_module(f"src.cogs.{module_name}")
            if hasattr(module, "setup"):
                await module.setup(bot)
                loaded_cogs.append(module_name)
            else:
                failed_cogs.append(f"{module_name} (no setup)")
        except Exception as e:
            failed_cogs.append(f"{module_name} ({str(e)})")

    if loaded_cogs:
        logger.info(f"⚙️ Loaded cogs: {', '.join(loaded_cogs)}")
    if failed_cogs:
        logger.error(f"❌ Failed to load cogs: {', '.join(failed_cogs)}")

    return loaded_cogs


async def load_all(bot) -> Tuple[Dict[str, object], List[str]]:
    """Loads all services and cogs."""
    logger.info("🚀 Starting bot initialization...")
    services = await load_services(bot)
    cogs = await load_cogs(bot)
    logger.info("✅ Bot initialization complete")
    return services, cogs
