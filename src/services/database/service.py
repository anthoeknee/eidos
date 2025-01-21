# src/services/database/service.py
from typing import Any, Optional, Dict, List
from src.core.module_manager import module
from src.utils import logger
from .surrealdb import Surreal


@module(
    name="database",
    module_type="service",
    description="Database service for handling all database operations",
    requires=[],
)
class DatabaseService:
    def __init__(self, bot):
        self.bot = bot
        self.db: Optional[Surreal] = None

    async def setup(self, bot, module_manager):
        """Initialize the database service."""
        self.bot = bot
        self.db = Surreal()
        await self.db.connect()
        logger.info("Database service initialized")

    async def close(self):
        """Close database connections."""
        if self.db:
            await self.db.close()
            logger.info("Database connections closed")

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SurrealQL query."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.query(query, params)

    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified table."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.create(table, data)

    async def select(
        self, table: str, record_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Select records from a table."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.select(table, record_id)

    async def update(
        self, table: str, record_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a record in the specified table."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.update(table, record_id, data)

    async def delete(self, table: str, record_id: str) -> Dict[str, Any]:
        """Delete a record from the specified table."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.delete(table, record_id)
