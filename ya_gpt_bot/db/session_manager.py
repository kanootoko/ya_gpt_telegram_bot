# """Database session manager is defined here."""

# from loguru import logger
# from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine


# class SessionManager:
#     """
#     A class that implements the necessary functionality for working with the database:
#     issuing sessions, storing and updating connection
#     """

#     def __init__(  # pylint: disable=too-many-arguments
#         self, host: str, port: int, user: str, password: str, database: str, pool_size: int, application_name: str
#     ) -> None:
#         """Perform database connections pool initialization."""
#         logger.info(
#             "Creating connection pool with max_size = {} on postgresql://{}@{}:{}/{}",
#             pool_size,
#             user,
#             host,
#             port,
#             database,
#         )
#         self.engine = create_async_engine(
#             f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
#             future=True,
#             pool_size=min(2, pool_size - 5),
#             max_overflow=5,
#             connect_args={"server_settings": {"application_name": "app_name"}},
#         )
#         self.application_name = application_name

#     async def shutdown(self) -> None:
#         """Dispose connection pool and deinitialize."""
#         await self.engine.dispose()

#     def connect(self) -> AsyncConnection:
#         """Get an async connection to the database."""
#         return self.engine.connect()
