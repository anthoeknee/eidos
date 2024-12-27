from abc import ABC, abstractmethod
from typing import Dict, Any, Callable


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(self, name: str, description: str, parameters: Dict):
        """Initialize a tool.

        Args:
            name: The name of the tool.
            description: A description of what the tool does.
            parameters: A dictionary describing the tool's parameters.
        """
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> Any:
        """Execute the tool's logic.

        Args:
            args: A dictionary of arguments for the tool.

        Returns:
            The result of the tool's execution.
        """
        pass

    def to_dict(self) -> Dict:
        """Convert the tool to a dictionary suitable for the Gemini API."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
