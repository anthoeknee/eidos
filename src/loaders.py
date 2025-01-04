import os
import importlib
from typing import List, Any, Optional, TypeVar
from discord.ext import commands
from pathlib import Path
from utils.logger import logger  # Import our custom logger

T = TypeVar("T")


class BaseLoader:
    """Base class for all loaders with common functionality."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._loaded_modules: dict[str, Any] = {}

    @property
    def loaded_modules(self) -> dict[str, Any]:
        """Get all loaded modules."""
        return self._loaded_modules

    def get_module(self, module_name: str) -> Optional[Any]:
        """Get a loaded module by name."""
        return self._loaded_modules.get(module_name)

    @staticmethod
    def discover_modules(directory: str, package: str) -> List[str]:
        """
        Automatically discover modules in a directory.

        Args:
            directory: Directory path relative to src/
            package: Base package name (e.g., 'cogs' or 'services')
        """
        modules = []
        base_path = Path(__file__).parent / directory

        for item in base_path.rglob("*.py"):
            if item.name.startswith("_"):
                continue

            relative_path = item.relative_to(base_path.parent)
            module_path = str(relative_path).replace(os.sep, ".")[:-3]  # Remove .py
            modules.append(module_path)

        return modules


class ServiceLoader(BaseLoader):
    """Enhanced service loader with automatic discovery and flexible class names."""

    async def load_services(
        self, service_modules: List[str], class_name: str = "Service"
    ) -> None:
        """
        Load and initialize services from a list of module paths.

        Args:
            service_modules: List of module paths
            class_name: Name of the service class to look for (default: "Service")
        """
        for module_path in service_modules:
            try:
                module = importlib.import_module(module_path)

                # Try to find the service class by convention, then by module name
                service_class = getattr(module, class_name, None)
                if service_class is None:
                    module_name = module_path.split(".")[-1]
                    class_candidates = [
                        f"{module_name.capitalize()}Service",
                        f"{module_name.capitalize()}",
                    ]
                    for candidate in class_candidates:
                        service_class = getattr(module, candidate, None)
                        if service_class:
                            break

                if not service_class:
                    raise AttributeError(
                        f"Could not find service class in {module_path}"
                    )

                service = service_class(self.bot)
                self._loaded_modules[module_path] = service

                if hasattr(service, "setup") and callable(getattr(service, "setup")):
                    await service.setup()

                logger.success(f"Loaded service: {module_path}")  # Changed to success

            except Exception as e:
                logger.error(f"Failed to load service {module_path}: {str(e)}")
                raise


class CogLoader(BaseLoader):
    """Enhanced cog loader with automatic discovery."""

    async def load_cogs(self, cog_modules: List[str]) -> None:
        """Load cogs from a list of module paths."""
        for module_path in cog_modules:
            try:
                await self.bot.load_extension(module_path)
                self._loaded_modules[module_path] = True
                logger.success(f"Loaded cog: {module_path}")  # Changed to success
            except Exception as e:
                logger.error(f"Failed to load cog {module_path}: {str(e)}")
                raise


async def load_all(
    bot: commands.Bot,
    *,
    services_dir: str = "services",
    cogs_dir: str = "cogs",
    skip_services: List[str] = None,
    skip_cogs: List[str] = None,
) -> tuple[ServiceLoader, CogLoader]:
    """
    Load all services and cogs for the bot automatically.

    Args:
        bot: The Discord bot instance
        services_dir: Directory name containing services (default: "services")
        cogs_dir: Directory name containing cogs (default: "cogs")
        skip_services: List of service module names to skip (optional)
        skip_cogs: List of cog module names to skip (optional)

    Returns:
        Tuple of (ServiceLoader, CogLoader) instances
    """
    skip_services = skip_services or []
    skip_cogs = skip_cogs or []

    service_loader = ServiceLoader(bot)
    cog_loader = CogLoader(bot)

    # Discover and filter services
    service_modules = service_loader.discover_modules(services_dir, services_dir)
    service_modules = [
        m for m in service_modules if m.split(".")[-1] not in skip_services
    ]

    # Discover and filter cogs
    cog_modules = cog_loader.discover_modules(cogs_dir, cogs_dir)
    cog_modules = [m for m in cog_modules if m.split(".")[-1] not in skip_cogs]

    # Load everything
    if service_modules:
        logger.info(f"Loading {len(service_modules)} services...")  # Added info log
        await service_loader.load_services(service_modules)

    if cog_modules:
        logger.info(f"Loading {len(cog_modules)} cogs...")  # Added info log
        await cog_loader.load_cogs(cog_modules)

    return service_loader, cog_loader
