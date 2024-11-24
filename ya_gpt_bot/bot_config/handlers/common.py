"""Group messages handlers are defined here."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message, MessageReactionUpdated, ReactionTypeEmoji
from loguru import logger as global_logger
from loguru._logger import Logger

from ya_gpt_bot.bot_config.filters import ArtGenerationRequest
from ya_gpt_bot.bot_config.texts import get_responses
from ya_gpt_bot.bot_config.utils.reactions import has_new_reaction
from ya_gpt_bot.bot_config.utils.response import reply_with_html_fallback
from ya_gpt_bot.bot_config.utils.text import strip_command_by_space
from ya_gpt_bot.db.entities.enums import UserStatus
from ya_gpt_bot.gpt.client import ArtClient
from ya_gpt_bot.services.dtos import ChatStatus
from ya_gpt_bot.services.user_preferences_service import UserPreferencesService
from ya_gpt_bot.services.user_service import UserService
from ya_gpt_bot.ya_gpt import exceptions as ya_exc

common_messages_router = Router(name="common_messages_router")

responses = get_responses()


@common_messages_router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Return help message to the user."""
    await message.reply(responses.help)


@common_messages_router.message(Command("commands"))
async def commands_list_command(message: Message) -> None:
    """Return commands list message to the user."""
    await message.reply(responses.commands)


@common_messages_router.message(Command("set_status", "set_user_status"))
async def set_user_status_command(message: Message, user_service: UserService, logger: Logger = global_logger) -> None:
    """Set user status if user has sufficient rights."""
    parts = strip_command_by_space(message.text).split()
    if len(parts) != 2 or not parts[0].isdecimal() or parts[1].upper() not in (s.value for s in UserStatus):
        await message.reply(responses.SetStatus.wrong_format_user)
        return
    other_user_id = int(parts[0])
    other_user_new_status = UserStatus(parts[1].upper())
    try:
        user_status = await user_service.get_user_status(message.from_user.id, False)
        other_user_status = await user_service.get_user_status(other_user_id, False)
    except RuntimeError as exc:
        logger.error(
            f"Exception on set_status from user {message.from_user.id} for user {other_user_id}"
            f" (status {other_user_new_status.value})"
        )
        await message.reply(responses.error(exc))
        return

    if (
        user_status == UserStatus.SUPERADMIN
        or user_status == UserStatus.ADMIN
        and (
            other_user_status not in (UserStatus.ADMIN, UserStatus.SUPERADMIN)
            and other_user_new_status not in (UserStatus.ADMIN, UserStatus.SUPERADMIN)
        )
    ):
        await user_service.set_user_status(other_user_id, other_user_new_status)
        await message.reply(responses.SetStatus.done)
        return
    await message.reply(responses.SetStatus.unsufficient_permissions)


@common_messages_router.message(Command("get_preferences"))
async def get_preferences_command(message: Message, user_preferences_service: UserPreferencesService) -> None:
    """Set temperature preference for user."""
    preferences = await user_preferences_service.get_preferences(message.from_user.id)
    await reply_with_html_fallback(
        message,
        responses.Preferences.format_preferences(
            preferences.temperature, preferences.instruction_text, preferences.timeout
        ),
    )


@common_messages_router.message(Command("set_temperature"))
async def set_temperature_command(message: Message, user_preferences_service: UserPreferencesService) -> None:
    """Set temperature preference for user."""
    text = strip_command_by_space(message.text or "")
    if text == "":
        await user_preferences_service.set_temperature(message.from_user.id, None)
        await message.reply(responses.Preferences.success_reset)
        return
    if not (text.count(".") <= 1 and text.replace(".", "").isdecimal()) or not 0.0 <= float(text) <= 1.0:
        await message.reply(responses.Preferences.wrong_format_temperature)
        return
    await user_preferences_service.set_temperature(message.from_user.id, float(text))
    await message.reply(responses.Preferences.success_updated)


@common_messages_router.message(Command("set_preprompt", "set_instruction_text", "set_instruction"))
async def set_instruction_text_command(message: Message, user_preferences_service: UserPreferencesService) -> None:
    """Set instruction text preference for user."""
    text = strip_command_by_space(message.text or "")
    if text == "":
        await user_preferences_service.set_instruction_text(message.from_user.id, None)
        await message.reply(responses.Preferences.success_reset)
        return
    if len(text) >= 1024:
        await message.reply(responses.Preferences.too_long_instruction_text)
        return
    await user_preferences_service.set_instruction_text(message.from_user.id, text)
    await message.reply(responses.Preferences.success_updated)


@common_messages_router.message(Command("set_timeout"))
async def set_timeout_command(message: Message, user_preferences_service: UserPreferencesService) -> None:
    """Set timeout preference for user."""
    text = strip_command_by_space(message.text or "")
    if text == "":
        await user_preferences_service.set_request_timeout(message.from_user.id, None)
        await message.reply(responses.Preferences.success_reset)
        return
    if not text.isdecimal():
        await message.reply(responses.Preferences.wrong_format_timeout)
        return
    await user_preferences_service.set_request_timeout(message.from_user.id, int(text))
    await message.reply(responses.Preferences.success_updated)


@common_messages_router.message(Command("reset_preferences"))
async def reset_preferences_command(message: Message, user_preferences_service: UserPreferencesService) -> None:
    """Reset preferences for user."""
    await user_preferences_service.reset_preferences(message.from_user.id)
    await message.reply(responses.Preferences.success_reset_all)


@common_messages_router.message_reaction()
async def delete_on_bad_reaction_from_admin(
    message_reaction: MessageReactionUpdated,
    user_service: UserService,
    logger: Logger = global_logger,
) -> None:
    """Reset preferences for user."""
    logger.debug("reaction event: {}", message_reaction)
    if has_new_reaction(message_reaction, "💩") and await user_service.get_user_status(
        message_reaction.user.id, message_reaction.chat.type == "private"
    ) in (UserStatus.ADMIN, UserStatus.SUPERADMIN):
        logger.info(
            "Deleting message with chat_id={}, id={} by reaction from user id={}",
            message_reaction.chat.id,
            message_reaction.message_id,
            message_reaction.user.id,
        )
        await message_reaction.bot.delete_message(message_reaction.chat.id, message_reaction.message_id)


@common_messages_router.message(ArtGenerationRequest())
async def art_generation_request(
    message: Message,
    user_service: UserService,
    art_client: ArtClient,
    text: str,
    logger: Logger = global_logger,
) -> None:
    """Handle image generation request sending given text as prompt to ArtService."""
    logger.info("Treating as a generation command from user: {}", message.text)
    user_status = await user_service.get_user_status(message.from_user.id, message.chat.type == "private")
    if message.chat.type != "private":
        chat_status = await user_service.get_chat_status(message.chat.id)
    else:
        chat_status = None
    if user_status == UserStatus.BLOCKED:
        await message.reply(responses.StatusOnGenerate.blocked)
        return
    if (
        user_status not in (UserStatus.SUPERADMIN, UserStatus.ADMIN, UserStatus.AUTHORIZED)
        and chat_status != ChatStatus.AUTHORIZED
    ):
        await message.reply(responses.StatusRequest.pending)

    await message.react([ReactionTypeEmoji(emoji="👀")])

    logger.info("Generating image for a given prompt: {}", text)
    try:
        img = await art_client.generate(text)
        logger.debug("Finished image generation")
        await message.reply_photo(BufferedInputFile(img, "generation.jpg"))
        await message.react([])
    except ya_exc.ArtInvalidPrompt:
        await message.reply(responses.invalid_prompt_error)
        await message.react([ReactionTypeEmoji(emoji="👎")])
    except ya_exc.GenerationTimeoutError:
        await message.reply(responses.timeout_error)
        await message.react([ReactionTypeEmoji(emoji="😢")])
