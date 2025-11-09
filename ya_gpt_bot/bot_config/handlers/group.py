"""Group/supergroup/etc chat messages handlers are defined here."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru._logger import Logger

from ya_gpt_bot.bot_config.filters import DirectMessage, GPTGenerationRequest
from ya_gpt_bot.bot_config.texts import get_responses
from ya_gpt_bot.bot_config.utils.response import reply_with_html_fallback
from ya_gpt_bot.bot_config.utils.text import strip_command_by_space
from ya_gpt_bot.db.entities.enums import ChatStatus, UserStatus
from ya_gpt_bot.gpt.client import GPTClient
from ya_gpt_bot.services.impl.conversation_service import ConversationService
from ya_gpt_bot.services.messages_service import MessagesService
from ya_gpt_bot.services.user_preferences_service import UserPreferencesService
from ya_gpt_bot.services.user_service import UserService

chat_messages_router = Router(name="group_messages_router")
chat_messages_router.message.filter(~DirectMessage())

responses = get_responses()

CONTEXT_LENGTH = 2**13


@chat_messages_router.message(Command("tg_id"))
async def get_tg_id_command(message: Message) -> None:
    """Return user id (current or replied to)."""
    if message.reply_to_message is not None:
        idx = message.reply_to_message.from_user.id
    else:
        idx = message.from_user.id
    await message.reply(responses.reply_user_id(idx, message.reply_to_message is None))


@chat_messages_router.message(Command("chat_id"))
async def get_chat_id_command(message: Message) -> None:
    """Return current chat id."""
    idx = message.chat.id
    await message.reply(responses.reply_chat_id(idx))


@chat_messages_router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Return help message to the user"""
    await message.reply(responses.help)


@chat_messages_router.message(Command("set_group_status", "set_chat_status"))
async def set_chat_status_command(message: Message, user_service: UserService, logger: Logger) -> None:
    """Set current chat status if user has sufficient rights."""
    text = strip_command_by_space(message.text)

    if text not in list(c.value for c in ChatStatus):
        await message.reply(responses.SetStatus.wrong_format_chat_in_chat)
        return
    chat_id = message.chat.id
    new_status = ChatStatus(text)
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


@chat_messages_router.message(GPTGenerationRequest())
async def text_generation_request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    message: Message,
    user_service: UserService,
    gpt_client: GPTClient,
    user_preferences_service: UserPreferencesService,
    messages_service: MessagesService,
    logger: Logger,
    text: str,
) -> None:
    """Handle text generation request sending full request to GPTService"""
    user_status = await user_service.get_user_status(message.from_user.id, False)
    chat_status = await user_service.get_chat_status(message.chat.id)
    if user_status == UserStatus.BLOCKED:
        await message.reply(responses.StatusOnGenerate.blocked)
        return
    if (
        user_status not in (UserStatus.SUPERADMIN, UserStatus.ADMIN, UserStatus.AUTHORIZED)
        and chat_status != ChatStatus.AUTHORIZED
    ):
        await message.reply(responses.StatusRequest.pending)

    logger.debug("Got generatinon request message: {}", text)
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
    preferences = await user_preferences_service.get_preferences(message.from_user.id)

    response = await gpt_client.request(
        [e.message for e in dialog], preferences.temperature, preferences.instruction_text, preferences.timeout
    )
    logger.debug("Generation response: {}", response)
    results = await reply_with_html_fallback(message, response)
    for result in results:
        await messages_service.save_message(
            result.message_id, result.reply_to_message.message_id, message.chat.id, response, True
        )


@chat_messages_router.message(Command("digest"))
async def digest_request(
    message: Message,
    conversation_service: ConversationService,
    gpt_client: GPTClient,
):
    """Launch chat digest and delete saved history."""
    chat_id = message.chat.id
    messages = await conversation_service.get_chat_messages_history(chat_id, CONTEXT_LENGTH)
    if not messages:
        await message.bot.send_message(chat_id, text="Что-то пошло не так - ни одно сообщение не попало в контекст")
        return
    model_response = await gpt_client.request(
        messages,
        creativity_override=0.0,
        instruction_text_override=conversation_service.get_instruction_prompt(),
    )
    await reply_with_html_fallback(message, model_response)
