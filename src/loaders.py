import os
import glob
import importlib
from typing import List, Tuple, Dict
from src.utils.logger import logger  # Import our custom logger


async def load_services(bot) -> Dict[str, object]:
    """Loads all services from the services directory."""
    service_dir = os.path.join(os.path.dirname(__file__), "services")
    loaded_services = {}
    service_names = []

    # First, try direct .py files
    for filename in glob.glob(os.path.join(service_dir, "*.py")):
        if filename.endswith("__init__.py"):
            continue
        module_name = os.path.splitext(os.path.basename(filename))[0]
        service_names.append(module_name)

    # Then, try subdirectories
    for dirname in next(os.walk(service_dir))[1]:
        if dirname.startswith("__"):
            continue
        service_names.append(dirname)

    logger.info(f"Attempting to load services: {', '.join(service_names)}")

    # Load services
    for service_name in service_names:
        try:
            if os.path.exists(os.path.join(service_dir, f"{service_name}.py")):
                module = importlib.import_module(f"src.services.{service_name}")
            else:
                module = importlib.import_module(f"src.services.{service_name}")
            if hasattr(module, "setup"):
                try:
                    service_instance = await module.setup(bot)
                    loaded_services[service_name] = service_instance
                except Exception as setup_error:
                    logger.error(
                        f"Failed during setup of service {service_name}: {setup_error}"
                    )
                    raise
            else:
                logger.warning(f"Service {service_name} has no setup function.")
        except Exception as e:
            logger.error(f"Failed to load service {service_name}: {e}")
            raise

    logger.info(f"Loaded services: {', '.join(loaded_services.keys())}")
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


async def load_all(bot) -> Tuple[Dict[str, object], List[str]]:
    """Loads all services and cogs."""
    services = await load_services(bot)
    cogs = await load_cogs(bot)
    return services, cogs
