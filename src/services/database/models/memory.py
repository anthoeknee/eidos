from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from src.services.database.models.base import Base
from src.services.database.types import Vector


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True)
    channel_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSONB, nullable=True)
    embedding = Column(Vector(dimensions=1024), nullable=False)
    memory_type = Column(String, nullable=False)
    reference_urls = Column(ARRAY(String), nullable=True)

    __table_args__ = (
        # Add any indexes here if needed
    )
