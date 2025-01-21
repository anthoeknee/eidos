# src/services/database/surrealdb.py
import asyncio
from typing import Any, Optional, Dict, List
from surrealdb import SurrealDB, Table
from src.utils.logger import logger
from src.core.config import config


class Surreal:
    def __init__(self):
        self.client = SurrealDB(
            url=f"ws://{config.surrealdb_host}:{config.surrealdb_port}"
        )
        self.connected = False

    async def connect(self):
        """Connect to the SurrealDB instance using config values."""
        try:
            await self.client.connect()
            await self.client.signin(
                {"user": config.surrealdb_username, "pass": config.surrealdb_password}
            )
            await self.client.use(config.surrealdb_namespace, config.surrealdb_database)
            self.connected = True
            logger.info("Connected to SurrealDB")
        except Exception as e:
            logger.error(f"Failed to connect to SurrealDB: {e}")
            raise

    async def close(self):
        """Close the database connection."""
        if self.connected:
            await self.client.close()
            self.connected = False
            logger.info("Closed SurrealDB connection")

    async def query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SurrealQL query."""
        try:
            result = await self.client.query(query, params)
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified table."""
        try:
            result = await self.client.create(Table(table), data)
            return result
        except Exception as e:
            logger.error(f"Create operation failed: {e}")
            raise

    async def select(
        self, table: str, record_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Select records from a table."""
        try:
            if record_id:
                result = await self.client.select(f"{table}:{record_id}")
                return (
                    result if isinstance(result, list) else [result] if result else []
                )
            else:
                return await self.client.select(Table(table))
        except Exception as e:
            logger.error(f"Select operation failed: {e}")
            raise

    async def update(
        self, table: str, record_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a record in the specified table."""
        try:
            result = await self.client.update(f"{table}:{record_id}", data)
            return result
        except Exception as e:
            logger.error(f"Update operation failed: {e}")
            raise

    async def delete(self, table: str, record_id: str) -> Dict[str, Any]:
        """Delete a record from the specified table."""
        try:
            result = await self.client.delete(f"{table}:{record_id}")
            return result
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            raise
