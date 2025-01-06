from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from alembic import command
from alembic.config import Config
from pathlib import Path
from src.config import config
from src.utils.logger import logger
from contextlib import contextmanager
from typing import Generator, Any, List, Type, Dict, Tuple
from sqlalchemy.orm.decl_api import DeclarativeMeta  # For type hinting
import os
import asyncio
from .types import Vector
from urllib.parse import urlparse
from alembic.script import ScriptDirectory


class PostgresService:
    def __init__(self, bot):
        self.bot = bot
        self.engine = None
        self.SessionLocal = None
        self.alembic_config = None

    async def setup(self):
        """Initialize the database connection and perform migrations."""
        try:
            logger.info("Starting PostgreSQL Database Setup...")

            db_url = config.POSTGRES_URL
            parsed_url = urlparse(db_url)

            connect_args = {
                "connect_timeout": 10,
                "options": "-c statement_timeout=10000",
            }

            if (
                parsed_url.hostname != "localhost"
                and not parsed_url.hostname.startswith("127.0.")
            ):
                connect_args["sslmode"] = "prefer"

            self.engine = create_engine(
                db_url,
                connect_args=connect_args,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
            )

            # Initialize Alembic configuration first
            self.alembic_config = Config("alembic.ini")

            with self.engine.connect() as conn:
                logger.info("Checking database status...")

                # Check if alembic_version table exists
                result = conn.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'alembic_version'
                    );
                """)
                )
                has_alembic_table = result.scalar()

                if has_alembic_table:
                    # Get current revision
                    current = conn.execute(
                        text("SELECT version_num FROM alembic_version")
                    ).scalar()

                    # Get head revision from migrations
                    script = ScriptDirectory.from_config(self.alembic_config)
                    head = script.get_current_head()

                    if current == head:
                        logger.info("Database is up to date, skipping migrations")
                        self.SessionLocal = sessionmaker(
                            autocommit=False, autoflush=False, bind=self.engine
                        )
                        return self
                    else:
                        logger.info(f"Database needs upgrade: {current} -> {head}")
                else:
                    logger.info("First-time database setup needed")

                # Run migrations if we get here
                logger.info("Running migrations...")
                try:
                    with self.engine.begin() as connection:
                        self.alembic_config.attributes["connection"] = connection
                        command.upgrade(self.alembic_config, "head")
                        logger.info("Database migrations completed successfully")
                except Exception as e:
                    logger.error(f"Migration failed: {e}")
                    raise

            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            logger.info("PostgreSQL Database Setup Complete!")
            return self

        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

    @contextmanager
    def session(self) -> Generator[Session, Any, None]:
        """Provide a transactional scope around a series of operations."""
        if not self.SessionLocal:
            raise Exception("Database session not initialized.")
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    async def _run_migrations(self):
        """Run database migrations using Alembic."""
        try:
            migrations_dir = Path(os.getcwd()) / "migrations"
            if not migrations_dir.exists():
                logger.warning(
                    "Migrations directory not found. Skipping database migrations."
                )
                return

            self.alembic_config = Config()
            self.alembic_config.set_main_option("script_location", str(migrations_dir))
            self.alembic_config.set_main_option("sqlalchemy.url", config.POSTGRES_URL)

            command.upgrade(self.alembic_config, "head")
            logger.info("Database migrations completed successfully")

        except Exception as e:
            logger.error(f"❌ Database migrations failed: {e}")
            raise

    def vector_similarity_search(
        self,
        session: Session,
        model: Type[DeclarativeMeta],
        vector_column: Vector,
        query_vector: List[float],
        limit: int = 5,
        filter_conditions: list = None,
    ):
        """
        Perform a vector similarity search using cosine distance.

        Args:
            session: SQLAlchemy session
            model: The SQLAlchemy model class to search in
            vector_column: The column containing the vectors
            query_vector: The vector to compare against (list of floats)
            limit: Maximum number of results to return
            filter_conditions: Optional list of additional filter conditions

        Returns:
            List of model instances ordered by similarity
        """
        try:
            query = session.query(model)

            if filter_conditions:
                for condition in filter_conditions:
                    query = query.filter(condition)

            results = (
                query.order_by(vector_column.cosine_distance(query_vector))
                .limit(limit)
                .all()
            )
            return results
        except SQLAlchemyError as e:
            logger.error(f"Vector similarity search failed: {e}")
            raise

    def batch_vector_insert(
        self, session: Session, model: Type[DeclarativeMeta], records: List[dict]
    ):
        """
        Efficiently insert multiple records with vector data.

        Args:
            session: SQLAlchemy session
            model: The SQLAlchemy model class
            records: List of dictionaries containing the record data
        """
        try:
            session.bulk_insert_mappings(model, records)
            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Batch vector insert failed: {e}")
            session.rollback()
            raise

    def create_vector_index(
        self,
        session: Session,
        table_name: str,
        column_name: str,
        index_type: str = "hnsw",
        distance_type: str = "cosine",
        lists: int = None,
        m: int = None,
        ef_construction: int = None,
    ):
        """
        Create a vector index for faster similarity searches.

        Args:
            session: Database session
            table_name: Name of the table
            column_name: Name of the vector column
            index_type: 'hnsw' or 'ivfflat'
            distance_type: 'cosine', 'l2', or 'ip' (inner product)
            lists: Number of lists for ivfflat
            m: Max number of connections for hnsw
            ef_construction: Size of dynamic candidate list for hnsw
        """
        try:
            index_name = f"{table_name}_{column_name}_vector_idx"

            # Choose operator based on distance type
            ops_mapping = {
                "cosine": "vector_cosine_ops",
                "l2": "vector_l2_ops",
                "ip": "vector_ip_ops",
            }
            operator = ops_mapping.get(distance_type, "vector_cosine_ops")

            # Build index creation SQL
            if index_type == "hnsw":
                params = []
                if m is not None:
                    params.append(f"m = {m}")
                if ef_construction is not None:
                    params.append(f"ef_construction = {ef_construction}")

                params_str = f"WITH ({', '.join(params)})" if params else ""
                sql = f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} USING hnsw({column_name} {operator}) {params_str}
                """
            else:  # ivfflat
                lists_str = f"WITH (lists = {lists})" if lists else ""
                sql = f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} USING ivfflat({column_name} {operator}) {lists_str}
                """

            session.execute(text(sql))
            session.commit()
            logger.info(
                f"Created vector index {index_name} on {table_name}.{column_name}"
            )

        except SQLAlchemyError as e:
            logger.error(f"Failed to create vector index: {e}")
            raise

    def vector_search(
        self,
        session: Session,
        model: Type[DeclarativeMeta],
        vector_column: Vector,
        query_vector: List[float],
        limit: int = 5,
        distance_type: str = "cosine",
        filters: List = None,
        min_similarity: float = None,
    ) -> List[Tuple[Any, float]]:
        """
        Enhanced vector similarity search with multiple distance metrics and filtering.

        Args:
            session: Database session
            model: SQLAlchemy model class
            vector_column: Vector column to search
            query_vector: Query vector
            limit: Maximum number of results
            distance_type: 'cosine', 'l2', or 'ip' (inner product)
            filters: List of SQLAlchemy filter conditions
            min_similarity: Minimum similarity threshold (optional)

        Returns:
            List of tuples (record, similarity_score)
        """
        try:
            # Choose distance operator
            distance_ops = {"cosine": "<=>", "l2": "<->", "ip": "<#>"}
            op = distance_ops.get(distance_type, "<=>")

            # Build query
            query = session.query(model, text(f"embedding {op} :vector AS distance"))

            # Apply filters if provided
            if filters:
                for filter_condition in filters:
                    query = query.filter(filter_condition)

            # Apply distance threshold if provided
            if min_similarity is not None:
                if distance_type == "ip":
                    query = query.filter(text("embedding <#> :vector >= :threshold"))
                else:
                    query = query.filter(text(f"embedding {op} :vector <= :threshold"))

            # Execute query
            results = (
                query.params(vector=query_vector, threshold=min_similarity)
                .order_by(text(f"embedding {op} :vector"))
                .limit(limit)
                .all()
            )

            return [(item[0], item[1]) for item in results]

        except SQLAlchemyError as e:
            logger.error(f"Vector search failed: {e}")
            raise

    def upsert_vectors(
        self,
        session: Session,
        model: Type[DeclarativeMeta],
        records: List[Dict[str, Any]],
        unique_columns: List[str],
    ):
        """
        Upsert vectors and associated data.

        Args:
            session: Database session
            model: SQLAlchemy model class
            records: List of dictionaries containing record data
            unique_columns: Columns that determine uniqueness for upserting
        """
        try:
            # Convert records to string format that Postgres can understand
            stmt = text(f"""
                INSERT INTO {model.__tablename__} ({','.join(records[0].keys())})
                VALUES ({','.join([':' + k for k in records[0].keys()])})
                ON CONFLICT ({','.join(unique_columns)})
                DO UPDATE SET {','.join([f"{k}=EXCLUDED.{k}"
                                       for k in records[0].keys()
                                       if k not in unique_columns])}
            """)

            session.execute(stmt, records)
            session.commit()

        except SQLAlchemyError as e:
            logger.error(f"Vector upsert failed: {e}")
            session.rollback()
            raise
