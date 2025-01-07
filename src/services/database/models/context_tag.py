from sqlalchemy import Column, Integer, String
from src.services.database.models.base import Base


class ContextTag(Base):
    __tablename__ = "context_tags"

    id = Column(Integer, primary_key=True)
    tag = Column(String, unique=True, nullable=False)
