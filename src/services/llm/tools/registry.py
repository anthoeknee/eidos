from typing import Dict, List, Any
from google.genai import types
from src.utils import logger
from .base import BaseTool
from .adapters import GoogleGenAIAdapter

log = logger.setup_logger("tool_registry")


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._adapter = GoogleGenAIAdapter()

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Get a registered tool by name."""
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        return self._tools[name]

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tools_config(self) -> List[types.Tool]:
        """Get tools in Gemini's format for model configuration."""
        return [tool.tool_config for tool in self._tools.values()]

    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a registered tool."""
        tool = self.get_tool(name)
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            log.error(f"Error executing tool {name}: {e}")
            raise

    async def handle_function_call(
        self, function_call: types.FunctionCall
    ) -> types.Content:
        """Handle a function call from the model."""
        result = await self.execute_tool(function_call.name, **function_call.args)
        return types.Content(
            role="function",
            parts=[
                types.Part.from_function_response(
                    name=function_call.name, response={"result": result}
                )
            ],
        )


# Create global registry instance
registry = ToolRegistry()
