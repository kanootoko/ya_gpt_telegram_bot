"""Message helpers are defined here."""

from typing import Callable, Iterable

from aiogram.types import Message


def get_should_ignore_func(prefixes: Iterable[str], postfixes: Iterable[str]) -> Callable[[Message], bool]:
    """Get function to check message prefix/postfix is stated in `prefixes`/`postfixes`."""
    prefixes = tuple(prefixes)
    postfixes = tuple(postfixes)

    def inner(message: Message) -> bool:
        text = message.text or message.caption or ""
        if text.startswith(prefixes) or text.endswith(postfixes):
            return True
        return False

    return inner


def form_system_text(
    ignore_quote: bool, message: Message, instruction_text: str | None, is_dialog_start: bool
) -> str | None:
    """Get system text when needed. Consists of:
    - instruction text if it is a new dialog
    - full reply message if `ignore_quote` is False and reply if not directed to self
    - reply quote if `ignore_quote` is set to False
    """
    system_text = ""
    sep = "-=-=-=-=-=-"

    if is_dialog_start:
        system_text = (
            "Ты - модель искусственного интеллекта внутри чата. Твоя задача - отвечать на запросы пользователей"
            " так, как они того просят. Далее будет представлен диалог с пользователем."
        )
        if instruction_text is not None:
            system_text += (
                f' Пожелания пользователя (далее в рамках ограничителей "{sep}"):\n{sep}\n{instruction_text}\n{sep}'
            )

    if ignore_quote:
        return system_text or None

    if message.reply_to_message is not None and (
        is_dialog_start or message.reply_to_message.from_user.id != message.bot.id
    ):
        text = message.reply_to_message.text or message.reply_to_message.caption
        if text != "":
            system_text = (
                "\n\nПользователь прикладывает сообщение из чата, ссылаясь на него"
                f' (далее в рамках ограничителей "{sep}"):\n{sep}\n{text}\n{sep}'
            )

    if message.quote is not None:
        system_text += (
            "\n\nПользователь ссылается на конкретную цитату из текста"
            f' (далее в рамках ограничителей "{sep}"):\n{sep}\n{message.quote.text}\n{sep}'
        )

    return system_text or None
