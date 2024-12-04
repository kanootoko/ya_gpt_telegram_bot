"""Bot configuration is defined here."""

from typing import NoReturn

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger as global_logger
from loguru._logger import Logger
from sqlalchemy.ext.asyncio import create_async_engine

from ya_gpt_bot.bot_config.middlewares.generation_request import TreatPrefixesMiddleware
from ya_gpt_bot.bot_config.middlewares.logging import LoggingMiddleware
from ya_gpt_bot.bot_config.middlewares.retrying import RetryingMiddleware
from ya_gpt_bot.bot_config.utils.messages import get_should_ignore_func
from ya_gpt_bot.config.app_config import AppConfig
from ya_gpt_bot.services.impl.conversation_service import ConversationService
from ya_gpt_bot.services.impl.messages_service import MessagesServicePostgres
from ya_gpt_bot.services.impl.user_preferences_service import UserPreferencesServicePostgres
from ya_gpt_bot.services.impl.user_service import UserServicePostgres

from .routers import routers_list


async def run_bot(config: AppConfig, logger: Logger = global_logger) -> NoReturn:
    """Launch bot handlers."""
    gpt_client = config.yc.get_gpt_client()
    art_client = config.yc.get_art_client()

    logger.info(
        "Creating connection pool with max_size = {} on postgresql://{}@{}:{}/{}",
        config.db.pool_size,
        config.db.user,
        config.db.host,
        config.db.port,
        config.db.name,
    )
    engine = create_async_engine(
        f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:"
        f" {config.db.port}/{config.db.name}",
        future=True,
        pool_size=min(2, config.db.pool_size - 5),
        max_overflow=5,
        connect_args={"server_settings": {"application_name": config.db.application_name}},
    )

    user_service = UserServicePostgres(engine)
    user_preferences_service = UserPreferencesServicePostgres(engine)
    messages_service = MessagesServicePostgres(engine)
    conversation_service = ConversationService(engine)

    dp = Dispatcher(
        gpt_client=gpt_client,
        art_client=art_client,
        user_service=user_service,
        user_preferences_service=user_preferences_service,
        messages_service=messages_service,
        conversation_service=conversation_service,
    )

    dp.include_routers(*routers_list)
    if "/question" not in config.tg_bot.gpt_trigger_prefixes:
        config.tg_bot.gpt_trigger_prefixes.append("/question")
    if "/generate" not in config.tg_bot.art_trigger_prefixes:
        config.tg_bot.art_trigger_prefixes.append("/generate")
    dp.message.outer_middleware(LoggingMiddleware(logger, 2))
    dp.message.outer_middleware(
        TreatPrefixesMiddleware(
            config.tg_bot.gpt_trigger_prefixes,
            config.tg_bot.art_trigger_prefixes,
            get_should_ignore_func(config.tg_bot.ignore_prefixes, config.tg_bot.ignore_postfixes),
        )
    )
    dp.message.outer_middleware(RetryingMiddleware(config.tg_bot.max_retry_count))

    bot = Bot(config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

    logger.info("Starting polling Telegram bot.")
    try:
        await dp.start_polling(bot)
    finally:
        await gpt_client.close()
        await art_client.close()
