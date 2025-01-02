from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.bot import EidosBot


class Service(ABC):
    """Base class for all services."""

    def __init__(self, bot: "EidosBot"):
        self.bot = bot

    @abstractmethod
    async def start(self):
        """Start the service."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the service."""
        pass
