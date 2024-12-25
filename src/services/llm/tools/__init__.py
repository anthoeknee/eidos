from .registry import registry
from .search import SearchTool

# Register the search tool
registry.register(SearchTool())
