from typing import Type, TypeVar, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.services.database.models.base import BaseModel
from src.utils.logger import logger

ModelType = TypeVar("ModelType", bound=BaseModel)


def get_by_id(session: Session, model: Type[ModelType], id: int) -> Optional[ModelType]:
    """Get a record by its ID."""
    try:
        return session.query(model).filter(model.id == id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting {model.__name__} by ID {id}: {e}")
        return None


def get_all(session: Session, model: Type[ModelType]) -> List[ModelType]:
    """Get all records of a model."""
    try:
        return session.query(model).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting all {model.__name__}: {e}")
        return []


def create(session: Session, model: Type[ModelType], **kwargs) -> Optional[ModelType]:
    """Create a new record."""
    try:
        new_record = model(**kwargs)
        session.add(new_record)
        session.commit()
        return new_record
    except SQLAlchemyError as e:
        logger.error(f"Error creating {model.__name__}: {e}")
        session.rollback()
        return None


def update(
    session: Session, model: Type[ModelType], id: int, **kwargs
) -> Optional[ModelType]:
    """Update an existing record."""
    try:
        record = get_by_id(session, model, id)
        if record:
            for key, value in kwargs.items():
                setattr(record, key, value)
            session.commit()
            return record
        else:
            logger.warning(f"{model.__name__} with ID {id} not found for update.")
            return None
    except SQLAlchemyError as e:
        logger.error(f"Error updating {model.__name__} with ID {id}: {e}")
        session.rollback()
        return None


def delete(session: Session, model: Type[ModelType], id: int) -> bool:
    """Delete a record by its ID."""
    try:
        record = get_by_id(session, model, id)
        if record:
            session.delete(record)
            session.commit()
            return True
        else:
            logger.warning(f"{model.__name__} with ID {id} not found for deletion.")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error deleting {model.__name__} with ID {id}: {e}")
        session.rollback()
        return False
