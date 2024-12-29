from discord.ext import commands
from typing import Optional, Dict, Any


class BaseCog(commands.Cog):
    """Base cog class that all cogs should inherit from."""

    def __init__(self):
        self.name: str = self.__class__.__name__
        self.description: str = self.__doc__ or "No description provided."
        self.category: str = "Uncategorized"
        self.emoji: str = "🔧"  # Default emoji
        self.hidden: bool = False
        self._extra_info: Dict[str, Any] = {}

    @property
    def info(self) -> Dict[str, Any]:
        """Returns a dictionary containing all cog information."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "emoji": self.emoji,
            "hidden": self.hidden,
            **self._extra_info,
        }

    def set_info(self, **kwargs) -> None:
        """Update cog information."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self._extra_info[key] = value
