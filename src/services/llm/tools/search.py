from typing import Dict
from google.genai.types import GoogleSearch
from .base import BaseTool
from google.genai import types


class SearchTool(BaseTool):
    def __init__(self):
        self._search = GoogleSearch()

    @property
    def name(self) -> str:
        return "google_search"

    @property
    def description(self) -> str:
        return "Search the internet for current information"

    @property
    def parameters(self) -> Dict:
        return {
            "query": {
                "type": "STRING",
                "description": "The search query to look up",
                "required": True,
            }
        }

    def to_schema(self) -> Dict:
        """Implement required abstract method."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": self.parameters,
                "required": ["query"],
            },
        }

    def to_tool(self) -> Dict:
        """Override to return Google's native search tool."""
        return {"google_search": self._search}

    async def execute(self, query: str) -> str:
        # Note: The actual search execution is handled internally by the Gemini model
        # This method won't be called directly as Google Search is a special tool
        pass

    @property
    def function_declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name="google_search",
            description="Search the internet for current information",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "The search query to look up",
                    },
                },
                "required": ["query"],
            },
        )

    @property
    def tool_config(self) -> types.Tool:
        """Override to use Google's native search configuration."""
        return types.Tool(
            google_search_configs=[types.GoogleSearchConfig(disable_attribution=False)]
        )
