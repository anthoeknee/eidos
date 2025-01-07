from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List


def get_or_create_tags(session: Session, tags: List[str]):
    """
    Retrieves existing tags or creates new ones in the database.

    Args:
        session: The database session.
        tags: A list of tag names to get or create.
    """
    for tag_name in tags:
        # Check if the tag already exists
        existing_tag = session.execute(
            text("SELECT id FROM context_tags WHERE name = :name"), {"name": tag_name}
        ).fetchone()

        if existing_tag is None:
            # Create the tag if it doesn't exist
            session.execute(
                text("INSERT INTO context_tags (name) VALUES (:name)"),
                {"name": tag_name},
            )

    # Commit the changes after processing all tags
    session.commit()
