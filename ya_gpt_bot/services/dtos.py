"""Data Transfer Objects are defined here."""
from dataclasses import dataclass
from enum import Enum


class UserStatus(Enum):
    """Status of user account."""

    SUPERADMIN = "SUPERADMIN"
    "User can edit other admin privelligies"

    ADMIN = "ADMIN"
    "User can administrate bot"

    AUTHORIZED = "AUTHORIZED"
    "User can send requests to bot"

    PENDING = "PENDING"
    "User is new and needs confirmation"

    UNAUTHORIZED = "UNAUTHORIZED"
    "User is not authorized to creare requests"

    BLOCKED = "BLOCKED"
    "User is blocked explicitly"

    REVERSE_BLOCKED = "REVERSE_BLOCKED"
    "User has blocked the bot"


class ChatStatus(Enum):
    """Status of chat account."""

    AUTHORIZED = "AUTHORIZED"
    "Any user of chat (except blocked) can send requests to bot"

    PENDING = "PENDING"
    "Chat is new and needs confirmation"

    UNAUTHORIZED = "UNAUTHORIZED"
    "Chat is not authorized to creare requests"

    BLOCKED = "BLOCKED"
    "Chat is blocked explicitly"


@dataclass
class UserPreferences:
    """User preferences which overrides bot defaults."""

    temperature: float | None = None
    instruction_text: str | None = None
    timeout: str | None = None
