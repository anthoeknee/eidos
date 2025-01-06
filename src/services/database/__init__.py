from .postgres import PostgresService


async def setup(bot):
    db_service = PostgresService(bot)
    await db_service.setup()
    return db_service
