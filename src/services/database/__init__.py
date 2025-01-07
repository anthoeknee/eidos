from src.services.database.postgres import PostgresService
from src.utils.logger import logger


async def setup(bot):
    """Setup the database service."""
    try:
        db_service = PostgresService(bot)
        await db_service.setup()
        bot.services["database"] = db_service
        return db_service
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}", exc_info=True)
        raise
