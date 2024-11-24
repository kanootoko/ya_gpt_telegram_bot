"""Text-related utilities are defined here."""


def strip_command_by_space(text: str, command_prefix: str | tuple[str, ...] | None = None) -> str:
    """Strip command removing part before the first space character. If text has no space in it,
    empty string is returned.
    """
    if text is None:
        return None
    if command_prefix is not None and not text.startswith(command_prefix):
        return text
    space_index = text.find(" ")
    if space_index != -1:
        return text[space_index + 1 :].strip()
    return ""
