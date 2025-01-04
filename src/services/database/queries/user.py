from sqlalchemy.orm import Session
from src.services.database.models.user import User
from src.services.database.queries.base import get_by_id, create
from typing import Optional


def get_user_by_discord_id(session: Session, discord_id: str) -> Optional[User]:
    """Get a user by their Discord ID."""
    return session.query(User).filter(User.discord_id == discord_id).first()


def create_user(session: Session, discord_id: str, username: str) -> Optional[User]:
    """Create a new user."""
    return create(session, User, discord_id=discord_id, username=username)
