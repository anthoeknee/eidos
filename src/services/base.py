from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseService(ABC):
    """
    Abstract base class for all services.
    """

    def __init__(self, **kwargs: Dict[str, Any]):
        """
        Initialize the service.

        Args:
            **kwargs: Keyword arguments for service initialization.
        """
        self.config = kwargs

    @abstractmethod
    async def start(self) -> None:
        """
        Start the service.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the service.
        """
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """
        Check if the service is healthy.

        Returns:
            bool: True if the service is healthy, False otherwise.
        """
        pass
