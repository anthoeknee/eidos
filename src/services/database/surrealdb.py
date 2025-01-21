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

    async def create(
        self, table: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new record in the specified table."""
        try:
            result = await self.client.create(Table(table), data, params)
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
        self,
        table: str,
        record_id: str,
        data: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update a record in the specified table."""
        try:
            result = await self.client.update(f"{table}:{record_id}", data, params)
            return result
        except Exception as e:
            logger.error(f"Update operation failed: {e}")
            raise

    async def delete(
        self, table: str, record_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Delete a record from the specified table."""
        try:
            result = await self.client.delete(f"{table}:{record_id}", params)
            return result
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            raise

    async def upsert(
        self, table: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upsert a record in the specified table."""
        try:
            result = await self.client.upsert(Table(table), data, params)
            return result
        except Exception as e:
            logger.error(f"Upsert operation failed: {e}")
            raise

    async def vector_similarity_search(
        self,
        table: str,
        vector_field: str,
        query_vector: List[float],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Perform a vector similarity search."""
        try:
            query = f"SELECT *, vector::distance::knn() AS dist FROM {table} WHERE {vector_field} <|{limit}|> $query_vector ORDER BY vector::distance::knn() ASC"
            params = {"query_vector": query_vector}
            result = await self.client.query(query, params)
            return result
        except Exception as e:
            logger.error(f"Vector similarity search failed: {e}")
            raise

    async def graph_traversal(
        self, start_record: str, traversal_path: str
    ) -> List[Dict[str, Any]]:
        """Perform a graph traversal."""
        try:
            query = f"SELECT {traversal_path} FROM {start_record}"
            result = await self.client.query(query)
            return result
        except Exception as e:
            logger.error(f"Graph traversal failed: {e}")
            raise

    async def live_query(self, query: str) -> str:
        """Start a live query and return the live query ID."""
        try:
            result = await self.client.live(query)
            return result
        except Exception as e:
            logger.error(f"Live query failed: {e}")
            raise

    async def kill_live_query(self, live_id: str):
        """Kill a live query by its ID."""
        try:
            await self.client.kill(live_id)
            logger.info(f"Live query {live_id} killed")
        except Exception as e:
            logger.error(f"Failed to kill live query {live_id}: {e}")
            raise

    def live_notifications(self, live_id: str):
        """Get the live query notifications queue."""
        return self.client.live_notifications(live_id)
