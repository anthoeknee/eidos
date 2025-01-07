from src.services.database.postgres import PostgresService


async def setup(bot):
    """Setup the database service."""
    db_service = PostgresService(bot)
    await db_service.setup()  # Actually call the setup method
    bot.services["database"] = db_service
    return db_service
