from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, REAL


class Vector(TypeDecorator):
    """
    Custom type for PostgreSQL vectors.
    Internally represented as an array of floats.
    """

    impl = ARRAY(REAL)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value if value is not None else []

    def process_result_value(self, value, dialect):
        return value if value is not None else []
