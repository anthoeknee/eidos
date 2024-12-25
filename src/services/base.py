from abc import ABC, abstractmethod


class BaseService(ABC):
    """Base class for all services in the application."""

    def __init__(self):
        """Initialize the service."""
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service. Must be implemented by subclasses."""
        self._initialized = True

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the service. Must be implemented by subclasses."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    def ensure_initialized(self) -> None:
        """Ensure the service is initialized before use."""
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} is not initialized")
