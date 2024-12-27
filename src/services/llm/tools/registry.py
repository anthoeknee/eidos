from typing import Dict, List, Type
from src.services.llm.tools.base import BaseTool


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: Type[BaseTool]) -> None:
        """Register a tool in the registry.

        Args:
            tool: The tool class to register.
        """
        instance = tool()
        if instance.name in self.tools:
            raise ValueError(f"Tool with name '{instance.name}' already registered.")
        self.tools[instance.name] = instance

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by its name.

        Args:
            name: The name of the tool to get.

        Returns:
            The tool instance.
        """
        if name not in self.tools:
            raise ValueError(f"Tool with name '{name}' not found.")
        return self.tools[name]

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools.

        Returns:
            A list of all registered tool instances.
        """
        return list(self.tools.values())

    def get_all_tool_dicts(self) -> List[Dict]:
        """Get all registered tools as dictionaries for the Gemini API.

        Returns:
            A list of dictionaries representing the tools.
        """
        return [tool.to_dict() for tool in self.get_all_tools()]
