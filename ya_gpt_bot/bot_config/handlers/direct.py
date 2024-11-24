"""Direct messages handlers are defined here."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from loguru import logger as global_logger
from loguru._logger import Logger

from ya_gpt_bot.bot_config.filters import DirectMessage, GPTGenerationRequest
from ya_gpt_bot.bot_config.texts import get_responses
from ya_gpt_bot.bot_config.utils.response import reply_with_html_fallback
from ya_gpt_bot.bot_config.utils.text import strip_command_by_space
from ya_gpt_bot.db.entities.enums import ChatStatus, UserStatus
from ya_gpt_bot.gpt.client import GPTClient
from ya_gpt_bot.services.messages_service import MessagesService
from ya_gpt_bot.services.user_preferences_service import UserPreferencesService
from ya_gpt_bot.services.user_service import UserService
from ya_gpt_bot.ya_gpt import exceptions as ya_exc

direct_messages_router = Router(name="direct_messages_router")
direct_messages_router.message.filter(DirectMessage())

responses = get_responses()


@direct_messages_router.message(CommandStart())
async def start_command(message: Message, user_service: UserService, logger: Logger = global_logger) -> None:
    """Start command handler - respond based on user status."""
    status = await user_service.get_user_status(message.from_user.id, True)
    logger.info("User {} sent /start command. User status - {}", message.from_user.id, status)
    await message.reply(responses.StatusRequest.get(status))


@direct_messages_router.message(Command("tg_id"))
async def get_tg_id_command(message: Message) -> None:
    """Return user id."""
    idx = message.from_user.id
    await message.reply(responses.reply_user_id(idx, True))


@direct_messages_router.message(Command("set_group_status"))
async def set_chat_status_command(
    message: Message,
    user_service: UserService,
    logger: Logger = global_logger,
) -> None:
    """Set chat status if user has sufficient rights."""
    parts = strip_command_by_space(message.text).split()
    if len(parts) != 2 or not parts[0].isdecimal() or parts[1].upper() not in list(ChatStatus):
        await message.reply(responses.SetStatus.wrong_format_chat_direct)
        return
    chat_id = int(parts[0])
    new_status = ChatStatus(parts[1].upper())
    try:
        user_status = await user_service.get_user_status(message.from_user.id, False)
    except RuntimeError as exc:
        logger.error(
            f"Exception on set_chat_status from user {message.from_user.id} for chat {chat_id}"
            f" (status {new_status.value})"
        )
        await message.reply(responses.error(exc))
        return

    if user_status in (UserStatus.SUPERADMIN, UserStatus.ADMIN):
        await user_service.set_chat_status(chat_id, new_status)
        logger.info("User {} updated chat {} status to {}", message.from_user.id, chat_id, new_status.value)
        await message.reply(responses.SetStatus.done)
        return
    await message.reply(responses.SetStatus.unsufficient_permissions)


@direct_messages_router.message(GPTGenerationRequest())
async def text_generation_request(  # pylint: disable=too-many-arguments
    message: Message,
    user_service: UserService,
    gpt_client: GPTClient,
    user_preferences_service: UserPreferencesService,
    messages_service: MessagesService,
    text: str,
    logger: Logger = global_logger,
) -> None:
    """Handle text generation request sending full request to GPTService."""
    logger.info("Treating as a generation command from user: {}", message.text)
    status = await user_service.get_user_status(message.from_user.id, False)
    if status in (UserStatus.BLOCKED, UserStatus.PENDING, UserStatus.UNAUTHORIZED):
        await message.reply(responses.StatusOnGenerate.get(status))
        return
    await messages_service.save_message(
        message.message_id,
        (message.reply_to_message.message_id if message.reply_to_message is not None else None),
        message.chat.id,
        text,
        False,
    )
    dialog = await messages_service.get_dialog(message.chat.id, message.message_id)
    logger.debug("Current dialog: {}", dialog)

    await message.bot.send_chat_action(message.chat.id, "typing")
    if text in ("", "None"):
        message.reply(responses.empty_request)
        return
    try:
        preferences = await user_preferences_service.get_preferences(message.from_user.id)
        response = await gpt_client.request(
            [e.message for e in dialog], preferences.temperature, preferences.instruction_text, preferences.timeout
        )
        logger.debug("Generation response: {}", response)
        result = await reply_with_html_fallback(message, response)
        await messages_service.save_message(result.message_id, message.message_id, message.chat.id, response, True)
    except ya_exc.GenerationTimeoutError:
        await message.reply(responses.timeout_error)
