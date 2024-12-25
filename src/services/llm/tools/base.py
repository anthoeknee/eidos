from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from google.genai.types import FunctionDeclaration, Tool
from google.genai import types


@dataclass
class ToolParameter:
    """Represents a parameter for a tool."""

    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    items: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @property
    def parameters(self) -> Optional[Dict[str, ToolParameter]]:
        """Tool parameters."""
        return None

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        pass

    @abstractmethod
    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to schema format for LLM consumption."""
        pass

    @property
    @abstractmethod
    def function_declaration(self) -> FunctionDeclaration:
        """Get the tool's function declaration for Gemini."""
        pass

    @property
    def tool_config(self) -> types.Tool:
        """Get the tool configuration for Gemini."""
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=self.name,
                    description=self.description,
                    parameters=self.parameters,
                )
            ]
        )
