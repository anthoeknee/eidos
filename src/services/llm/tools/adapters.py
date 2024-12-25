from google import genai
from google.genai import types

from .base import BaseTool


class GoogleGenAIAdapter:
    """Adapts tools to Google's format."""

    def to_tool(self, tool: BaseTool) -> types.Tool:
        """Convert a tool to Google's format."""
        if tool.name == "google_search":
            # Special case for search tool
            return types.Tool(
                google_search_configs=[
                    types.GoogleSearchConfig(disable_attribution=False)
                ]
            )

        # Regular tools
        return types.Tool(
            function_declarations=[
                genai.types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=genai.types.Schema(
                        type=genai.types.SchemaType.OBJECT,
                        properties={
                            name: genai.types.Schema(
                                type=genai.types.SchemaType[param.type.upper()],
                                description=param.description,
                            )
                            for name, param in tool.parameters.items()
                        },
                        required=[
                            name
                            for name, param in tool.parameters.items()
                            if param.required
                        ],
                    ),
                )
            ]
        )
