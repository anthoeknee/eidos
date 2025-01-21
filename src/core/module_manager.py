# src/core/module_manager.py
import importlib
from pathlib import Path
from src.utils.logger import logger
from typing import Set, Dict, Any, Callable, Type, Optional, List
from collections import defaultdict


def module(
    name: str,
    module_type: str,
    description: Optional[str] = None,
    help_text: Optional[str] = None,
    requires: Optional[List[str]] = None,
) -> Callable:
    """
    Decorator for modules to store metadata and handle dependencies.
    """

    def decorator(cls: Type) -> Type:
        """Inner decorator function."""
        cls.module_metadata = {
            "name": name,
            "type": module_type,
            "description": description,
            "help_text": help_text,
            "requires": requires or [],
        }
        return cls

    return decorator


class ModuleManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.bot = None
        self.loaded_modules: Set[str] = set()
        self.module_instances: Dict[str, Any] = {}
        self.module_metadata: Dict[str, Dict[str, Any]] = {}
        self._loading_in_progress = False
        self.module_registry: Dict[str, List[Any]] = defaultdict(list)

    def set_bot(self, bot):
        """Set the bot instance."""
        self.bot = bot

    def register_plugin(self, plugin_type: str, plugin: Any):
        """Register a plugin with the module manager."""
        self.module_registry[plugin_type].append(plugin)

    def get_plugins(self, plugin_type: str) -> List[Any]:
        """Get all plugins of a specific type."""
        return self.module_registry.get(plugin_type, [])

    async def load_modules(self) -> None:
        """Load all modules from the modules directory."""
        if self._loading_in_progress:
            return

        self._loading_in_progress = True

        try:
            all_modules = []
            for file_path in self.base_dir.rglob("*.py"):
                if file_path.name != "__init__.py":
                    all_modules.append(file_path)

            sorted_modules = await self._sort_modules_by_dependency(all_modules)

            for file_path in sorted_modules:
                is_service = "services" in str(file_path)
                await self._load_module(file_path, is_service=is_service)

            logger.info(f"Loaded {len(self.loaded_modules)} unique modules")
            logger.info(f"Loaded modules: {list(self.loaded_modules)}")

        except Exception as e:
            logger.error(f"Error during module loading: {str(e)}")
            raise

        finally:
            self._loading_in_progress = False

    async def _sort_modules_by_dependency(self, module_paths: List[Path]) -> List[Path]:
        """Sort modules based on their dependencies."""
        module_names = {}
        dependencies = defaultdict(list)

        for file_path in module_paths:
            module_name = file_path.stem
            relative_path = file_path.relative_to(self.base_dir.parent)
            import_path = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

            try:
                module = importlib.import_module(import_path)
                if hasattr(module, "module_metadata"):
                    metadata = module.module_metadata
                    module_names[module_name] = file_path
                    dependencies[module_name] = metadata.get("requires", [])
                    self.module_metadata[module_name] = metadata
                else:
                    logger.warning(f"Module {module_name} has no metadata")
            except Exception as e:
                logger.error(
                    f"Error importing module {module_name} for dependency check: {e}"
                )
                continue

        sorted_modules = []
        visited = set()

        async def visit(module_name):
            if module_name in visited:
                return
            visited.add(module_name)
            for dep in dependencies[module_name]:
                await visit(dep)
            if module_name in module_names:
                sorted_modules.append(module_names[module_name])

        for module_name in module_names:
            await visit(module_name)

        return sorted_modules

    async def _load_module(self, file_path: Path, is_service: bool) -> bool:
        """Load a single module."""
        try:
            module_name = file_path.stem
            if module_name in self.loaded_modules:
                return False

            relative_path = file_path.relative_to(self.base_dir.parent)
            import_path = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

            if is_service:
                logger.debug(f"Attempting to import module: {import_path}")
                module = importlib.import_module(import_path)
                self.module_instances[module_name] = module
                logger.debug(f"Successfully imported module: {module_name}")

                if hasattr(module, "setup"):
                    logger.debug(
                        f"Found setup function in {module_name}, calling it..."
                    )
                    try:
                        await module.setup(self.bot, self)
                        logger.debug(f"Setup completed for {module_name}")
                    except Exception as e:
                        logger.error(f"Error during setup of {module_name}: {e}")
                        raise
                else:
                    logger.error(f"No setup function found in {module_name}")
                    return False
            else:
                await self.bot.load_extension(import_path)
                logger.debug(f"Loaded cog: {module_name} from {file_path}")

            self.loaded_modules.add(module_name)
            return True

        except Exception as e:
            logger.error(f"Error loading module {file_path}: {str(e)}")
            logger.error("Full error details:", exc_info=True)
            return False

    def get_module(self, module_name: str) -> Any:
        """Get a loaded module instance by name."""
        return self.module_instances.get(module_name)

    def list_modules(self) -> list[str]:
        """Return list of loaded module names."""
        return list(self.loaded_modules)

    async def initialize_bot(self):
        """Initialize the bot after all modules are loaded."""
        await self._register_event_handlers()
        await self._register_command_handlers()

    async def _register_event_handlers(self):
        """Register event handlers from loaded modules."""
        event_handlers = self.get_plugins("event_handler")
        for handler in event_handlers:
            if hasattr(handler, "register_events"):
                await handler.register_events(self.bot)
            else:
                logger.warning(
                    f"Event handler {handler} has no register_events method."
                )

    async def _register_command_handlers(self):
        """Register command handlers from loaded modules."""
        command_handlers = self.get_plugins("command_handler")
        for handler in command_handlers:
            if hasattr(handler, "register_commands"):
                await handler.register_commands(self.bot)
            else:
                logger.warning(
                    f"Command handler {handler} has no register_commands method."
                )
