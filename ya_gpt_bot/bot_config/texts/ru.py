# pylint: disable=too-few-public-methods,redefined-builtin,invalid-name
"""Russian responses are defined here."""

import traceback

from loguru import logger as global_logger
from loguru._logger import Logger

from ya_gpt_bot.db.entities.enums import ChatStatus, UserStatus


class StatusRequest:
    """Status request responses"""

    superadmin = "Вы можете управлять администраторами бота."
    admin = "Вы являетесь администратором бота"
    authorized = "Доступ разрешен"
    pending = "Ваш статус - в ожидании получения доступа"
    unauthorized = "Доступ к функционалу бота запрещен"
    blocked = "Доступ был заблокирован"
    reverse_blocked = "Вы заблокировали бота (если этот статус отображается, то это ошибка)"

    @staticmethod
    def get(user_status: UserStatus) -> str:
        """Return response of status request for a user with a given status."""
        return getattr(StatusRequest, user_status.value.lower(), f"Ваш статус неизвестен ({user_status.value})")


class StatusOnGenerate:
    """Status request responses"""

    pending = "Для выполнения запросов дождитесь подтверждения статуса"
    unauthorized = "Доступ к функционалу бота не был подтвержден"
    blocked = "Доступ у функционалу бота был заблокирован"
    reverse_blocked = "Вы заблокировали бота (если этот статус отображается, то это ошибка)"

    @staticmethod
    def get(user_status: UserStatus) -> str:
        """Return response of status request for a user with a given status."""
        return getattr(StatusRequest, user_status.value.lower(), f"Ваш статус неизвестен ({user_status.value})")


class SetStatus:
    """Set status command responses"""

    wrong_format_user = (
        "Ошибка в формате ввода. Корректный запрос: **:user_tg_id: <status>**, варианты статуса: "
        f"{', '.join(st.value for st in UserStatus if st != UserStatus.SUPERADMIN)}."
    )
    wrong_format_chat_direct = (
        "Ошибка в формате ввода. Корректный запрос на смену статуса заданного чата: **<chat_tg_id> <status>**,"
        f" варианты статуса: {', '.join(st.value for st in ChatStatus)}."
    )
    wrong_format_chat_in_chat = (
        "Ошибка в формате ввода. Корректный запрос на смену статуса текущего чата: /set_group_status **:status:**,"
        " варианты статуса: "
        f"{', '.join(st.value for st in ChatStatus)}"
    )
    done = "Статус обновлен"
    unsufficient_permissions = "Недостаточно прав для данного изменения статуса"


class Preferences:
    """Set user preferences command responses"""

    wrong_format_temperature = "Неверный формат значения, необходимо вещественное число в пределах от 0.0 до 1.0."
    too_long_instruction_text = "Ограничение сверху на длину текста - 1024 символа."
    wrong_format_timeout = "Неверный формат значения, необходимо целое число."
    success_updated = "Значение параметра обновлено."
    success_reset = "Значение параметра сброшено."
    success_reset_all = "Значения всех параметров сброшены."

    @staticmethod
    def format_preferences(temperature: str | None, instruction_text: str | None, timeout: int | None) -> str:
        """Return formatted preferences string."""
        if temperature is None and instruction_text is None and timeout is None:
            return "Используются настройки по-умолчанию"
        return "Текущие значения настроек пользователя:\n" + "\n".join(
            [
                (f" - temperature: {temperature}" if temperature is not None else ""),
                (f" - instruction_text: {instruction_text}" if instruction_text is not None else ""),
                (f" - timeout: {timeout}" if timeout is not None else ""),
            ]
        )


help = (
    "Данный бот предназначен для предоставления доступа к YandexGPT и YandexART через Телеграм.\n"
    "Для того, чтобы получать ответы на запросы, необходимо получить личный доступ или "
    "выполнять запросы в авторизованном чате (и не быть при этом забаненным лично).\n\n"
    "Список доступных команд можно получить с помощью **/commands**"
)

commands = """
Список доступных комманд пользователей:

**/question** и префикс "Алиса" - запрос в YandexGPT
**/generate** и префикс "Алиса, нарисуй" - запрос в YandexART

**/set_temperature** - установить температуру ответа (0.0 - максимально точен к запросу и краток, 1.0 - больший полет фантазии)
**/set_instructions** - установить пре-промпт к своим запросам
**/reset_preferences** - сбросить значения параметустановить таймаут на выполнение своих запросов (для дебага)ров в значения по умолчанию
**/set_timeout** - установить таймаут на выполнение своих запросов (для дебага)
**/get_preferences** - получить значения своих личных настроек

**/tg_id **- получить значение своего идентификатора Telegram
**/chat_id **- получить значение идентификатора чата

Команды администрирования:

**/set_user_status** __:user_tg_id:__ __:status:__ - установить статус пользователю
**/set_group_status** __:chat_tg_id:__ __:status:__ (или просто __:status:__ в чате) - установить статус чата
""".strip()

timeout_error = (
    "Не удалось получить ответ за отведенное время, попробуйте упростить запрос или попробовать еще раз позже."
)

empty_request = "Передан пустой запрос."

no_handler_available = "Произошла ошибка, запрос не может быть корректно обработан."

invalid_prompt_error = "Данный запрос не может быть обработан. Попробуйте сменить формулировку."


def reply_user_id(user_id: int, direct_user: bool) -> str:
    """Return string explaining which user_id is returned.

    :param direct_user: indicates that this is id of user itself, otherwise - of user of replied message.
    """
    if direct_user:
        return f"Ваш идентификатор: {user_id}"
    return f"Идентификатор заданного пользователя: {user_id}"


def reply_chat_id(group_id: int) -> str:
    """Return group id reply."""
    return f"Идентификатор текущей группы: {group_id}"


def error(exc: Exception, logger: Logger = global_logger) -> str:
    """Return exception info."""
    logger.error("Exception occured: {!r}", exc)
    logger.debug("Traceback: {}", traceback.format_exc())
    return "Произошла программная ошибка, невозможно обработать запрос"
