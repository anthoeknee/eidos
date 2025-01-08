from sqlalchemy.types import TypeDecorator, Text
import numpy as np


class Vector(TypeDecorator):
    """Custom type for PostgreSQL vectors using pgvector"""

    impl = Text
    cache_ok = True

    def __init__(self, dimensions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dimensions = dimensions

    def process_bind_param(self, value, dialect):
        """Convert Python list to PostgreSQL vector string format"""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, (list, np.ndarray)):
            return f"[{','.join(str(x) for x in value)}]"
        raise ValueError(f"Unsupported type for vector: {type(value)}")

    def process_result_value(self, value, dialect):
        """Convert PostgreSQL vector string format back to Python list"""
        if value is None:
            return None
        if isinstance(value, str):
            # Remove brackets and split by commas
            return [float(x) for x in value[1:-1].split(",")]
        return value

    def get_col_spec(self, **kw):
        if self.dimensions:
            return f"vector({self.dimensions})"
        return "vector"
