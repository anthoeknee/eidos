import asyncio
import importlib
import inspect
import os
from typing import List

from src.core.bot import EidosBot
from src.services.base import Service
from src.utils.logger import logger


class ServiceManager:
    """Manages the loading and unloading of services."""

    def __init__(self, bot: EidosBot, service_dir: str = "src/services"):
        self.bot = bot
        self.service_dir = service_dir
        self.services: List[Service] = []

    async def load_services(self):
        """Loads all services from the service directory."""
        logger.info("Loading services...")
        for module_name in self._discover_services():
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, Service)
                        and obj != Service
                    ):
                        service_instance = obj(self.bot)
                        self.services.append(service_instance)
                        logger.info(f"Loaded service: {name}")
            except Exception as e:
                logger.error(f"Failed to load service from {module_name}: {e}")

        await asyncio.gather(*(service.start() for service in self.services))
        logger.info("All services loaded and started.")

    async def unload_services(self):
        """Unloads all loaded services."""
        logger.info("Unloading services...")
        await asyncio.gather(*(service.stop() for service in reversed(self.services)))
        self.services.clear()
        logger.info("All services unloaded.")

    def _discover_services(self) -> List[str]:
        """Discovers service modules in the service directory."""
        service_modules = []
        for root, _, files in os.walk(self.service_dir):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    module_path = os.path.join(root, file)
                    module_name = (
                        module_path.replace(os.sep, ".")
                        .replace(".py", "")
                        .replace("src.", "")
                    )
                    service_modules.append(module_name)
        return service_modules
