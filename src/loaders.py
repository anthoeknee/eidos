import os
import glob
import importlib
from typing import List
from src.utils.logger import logger  # Import our custom logger


async def load_services(bot) -> List[str]:
    """Loads all services from the services directory."""
    service_dir = os.path.join(os.path.dirname(__file__), "services")
    loaded_services = []
    for filename in glob.glob(os.path.join(service_dir, "*.py")):
        if filename.endswith("__init__.py"):
            continue
        module_name = os.path.splitext(os.path.basename(filename))[0]
        try:
            module = importlib.import_module(f"src.services.{module_name}")
            if hasattr(module, "setup"):
                await module.setup(bot)
                loaded_services.append(module_name)
                logger.info(f"Loaded service: {module_name}")
            else:
                logger.warning(f"Service {module_name} has no setup function.")
        except Exception as e:
            logger.error(f"Failed to load service {module_name}: {e}")
    return loaded_services


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


async def load_all(bot) -> tuple[List[str], List[str]]:
    """Loads all services and cogs."""
    services = await load_services(bot)
    cogs = await load_cogs(bot)
    return services, cogs
