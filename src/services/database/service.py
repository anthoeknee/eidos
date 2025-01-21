from typing import Any, Optional, Dict, List
from src.core.module_manager import module
from src.utils import logger
from .surrealdb import Surreal
from google import genai
from src.core.config import config


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
        genai.configure(api_key=config.google_api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.embedding_model = genai.GenerativeModel("models/embedding-001")

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

    async def create(
        self, table: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new record in the specified table."""
        if not self.db:
            raise RuntimeError("Database not initialized")

        # Generate embedding if content is present
        if "content" in data:
            data["embedding"] = await self._generate_embedding(data["content"])

        return await self.db.create(table, data, params)

    async def select(
        self, table: str, record_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Select records from a table."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.select(table, record_id)

    async def update(
        self,
        table: str,
        record_id: str,
        data: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update a record in the specified table."""
        if not self.db:
            raise RuntimeError("Database not initialized")

        # Generate embedding if content is present
        if "content" in data:
            data["embedding"] = await self._generate_embedding(data["content"])

        return await self.db.update(table, record_id, data, params)

    async def delete(
        self, table: str, record_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Delete a record from the specified table."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.delete(table, record_id, params)

    async def upsert(
        self, table: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upsert a record in the specified table."""
        if not self.db:
            raise RuntimeError("Database not initialized")

        # Generate embedding if content is present
        if "content" in data:
            data["embedding"] = await self._generate_embedding(data["content"])

        return await self.db.upsert(table, data, params)

    async def vector_similarity_search(
        self,
        table: str,
        vector_field: str,
        query_vector: List[float],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Perform a vector similarity search."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.vector_similarity_search(
            table, vector_field, query_vector, limit
        )

    async def graph_traversal(
        self, start_record: str, traversal_path: str
    ) -> List[Dict[str, Any]]:
        """Perform a graph traversal."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.graph_traversal(start_record, traversal_path)

    async def live_query(self, query: str) -> str:
        """Start a live query and return the live query ID."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.live_query(query)

    async def kill_live_query(self, live_id: str):
        """Kill a live query by its ID."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        await self.db.kill_live_query(live_id)

    def live_notifications(self, live_id: str):
        """Get the live query notifications queue."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return self.db.live_notifications(live_id)

    async def query_with_llm(self, natural_language_query: str) -> List[Dict[str, Any]]:
        """
        Translates a natural language query into SurrealQL and executes it.
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        prompt = f"""
        Translate the following natural language query into a SurrealQL query.
        Do not include any explanation or surrounding text, only the SurrealQL query.
        Natural Language Query: {natural_language_query}
        """
        try:
            response = self.model.generate_content(prompt)
            surrealql_query = response.text.strip()
            logger.info(f"Generated SurrealQL query: {surrealql_query}")
            return await self.execute_query(surrealql_query)
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generates a vector embedding for the given text."""
        try:
            response = await self.embedding_model.generate_content_async(text)
            return response.embedding.values
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def search_and_prompt_llm(
        self, table: str, vector_field: str, query: str, limit: int = 5
    ) -> str:
        """
        Searches for relevant content using vector similarity and prompts the LLM.
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        query_embedding = await self._generate_embedding(query)

        results = await self.vector_similarity_search(
            table, vector_field, query_embedding, limit
        )

        if not results:
            return "No relevant information found."

        context = "\n".join([result.get("content", "") for result in results])

        prompt = f"""
        You are a helpful AI assistant. Use the following context to answer the user's question.
        If the context does not contain the answer, respond with "I don't know".

        Context:
        {context}

        Question: {query}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"LLM prompting failed: {e}")
            raise
