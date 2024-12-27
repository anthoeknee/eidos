from typing import Dict, Any
from src.services.llm.tools.base import BaseTool


class ExampleTool(BaseTool):
    """Example tool that multiplies two numbers."""

    def __init__(self):
        """Initialize the example tool."""
        super().__init__(
            name="multiply",
            description="Returns the product of two numbers.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "a": {"type": "NUMBER", "description": "The first number."},
                    "b": {"type": "NUMBER", "description": "The second number."},
                },
                "required": ["a", "b"],
            },
        )

    async def execute(self, args: Dict[str, Any]) -> Any:
        """Multiply two numbers.

        Args:
            args: A dictionary containing 'a' and 'b'.

        Returns:
            The product of a and b.
        """
        a = args.get("a")
        b = args.get("b")

        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Both 'a' and 'b' must be numbers.")

        return a * b
