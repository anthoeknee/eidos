import asyncpg
from typing import Any, Dict, List, Optional
from src.services.storage.base import BaseStorageService
from src.core.config import settings
from src.utils.logger import Logger


class PostgresService(BaseStorageService):
    """PostgreSQL database service implementation."""

    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)
        self._pool: Optional[asyncpg.Pool] = None
        self._url = settings.postgres_url
        self.logger = Logger(name="PostgresService")

    async def connect(self) -> None:
        """Connect to the PostgreSQL database."""
        try:
            self._pool = await asyncpg.create_pool(self._url)
            self.logger.info("Connected to PostgreSQL")
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the PostgreSQL database."""
        if self._pool:
            await self._pool.close()
            self.logger.info("Disconnected from PostgreSQL")

    async def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """Create a table in the database."""
        if not self._pool:
            raise Exception("Not connected to PostgreSQL")

        column_definitions = ", ".join(
            f"{name} {type}" for name, type in columns.items()
        )
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions})"
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(sql)
            self.logger.info(f"Created table {table_name}")
        except Exception as e:
            self.logger.error(f"Failed to create table {table_name}: {e}")
            raise

    async def insert(self, table_name: str, data: Dict[str, Any]) -> None:
        """Insert data into a table."""
        if not self._pool:
            raise Exception("Not connected to PostgreSQL")

        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(sql, *data.values())
            self.logger.debug(f"Inserted data into {table_name}: {data}")
        except Exception as e:
            self.logger.error(f"Failed to insert data into {table_name}: {e}")
            raise

    async def get_by_id(self, table_name: str, id: Any) -> Optional[Dict[str, Any]]:
        """Get a record by its ID."""
        if not self._pool:
            raise Exception("Not connected to PostgreSQL")

        sql = f"SELECT * FROM {table_name} WHERE id = $1"
        try:
            async with self._pool.acquire() as conn:
                record = await conn.fetchrow(sql, id)
                return dict(record) if record else None
        except Exception as e:
            self.logger.error(
                f"Failed to get record from {table_name} with id {id}: {e}"
            )
            raise

    async def update(self, table_name: str, id: Any, data: Dict[str, Any]) -> None:
        """Update a record in a table."""
        if not self._pool:
            raise Exception("Not connected to PostgreSQL")

        set_values = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(data.keys()))
        sql = f"UPDATE {table_name} SET {set_values} WHERE id = $1"
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(sql, id, *data.values())
            self.logger.debug(f"Updated record in {table_name} with id {id}: {data}")
        except Exception as e:
            self.logger.error(
                f"Failed to update record in {table_name} with id {id}: {e}"
            )
            raise

    async def delete(self, table_name: str, id: Any) -> None:
        """Delete a record from a table."""
        if not self._pool:
            raise Exception("Not connected to PostgreSQL")

        sql = f"DELETE FROM {table_name} WHERE id = $1"
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(sql, id)
            self.logger.debug(f"Deleted record from {table_name} with id {id}")
        except Exception as e:
            self.logger.error(
                f"Failed to delete record from {table_name} with id {id}: {e}"
            )
            raise

    async def list(
        self, table_name: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List records from a table."""
        if not self._pool:
            raise Exception("Not connected to PostgreSQL")

        sql = f"SELECT * FROM {table_name} LIMIT $1 OFFSET $2"
        try:
            async with self._pool.acquire() as conn:
                records = await conn.fetch(sql, limit, offset)
                return [dict(record) for record in records]
        except Exception as e:
            self.logger.error(f"Failed to list records from {table_name}: {e}")
            raise

    async def query(
        self, sql: str, params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a custom SQL query."""
        if not self._pool:
            raise Exception("Not connected to PostgreSQL")

        try:
            async with self._pool.acquire() as conn:
                records = await conn.fetch(sql, *params if params else [])
                return [dict(record) for record in records]
        except Exception as e:
            self.logger.error(
                f"Failed to execute query: {sql} with params {params}: {e}"
            )
            raise

    async def is_healthy(self) -> bool:
        """Check if the database connection is healthy."""
        if not self._pool:
            return False
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def start(self) -> None:
        """Start the service by connecting to PostgreSQL."""
        await self.connect()

    async def stop(self) -> None:
        """Stop the service by disconnecting from PostgreSQL."""
        await self.disconnect()
