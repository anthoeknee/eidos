from src.services.database.postgres import PostgresService


async def setup(bot):
    """Setup the database service."""
    db_service = PostgresService(bot)  # The constructor handles initialization
    bot.services["database"] = db_service
    return db_service
