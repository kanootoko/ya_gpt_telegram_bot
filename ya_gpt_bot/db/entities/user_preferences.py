"""Users preferences table is defined here."""
from typing import Callable

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, String, Table

from ya_gpt_bot.db.metadata import metadata

func: Callable

t_user_preferences = Table(
    "users_preferences",
    metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True, nullable=False),
    Column(
        "temperature", Float, CheckConstraint("temperature >= 0.0 AND temperature <= 1.0", "temperature_constraint")
    ),
    Column("instruction_text", String(1024)),
    Column("timeout", Integer),
)
"""Users preferences which are used over bot defaults.

Columns:
- `user_id` - user identifier, big integer
- `temperature` - temperature of YaGPT generation, float, 0.0 <= value <= 1.0
- `instruction_text` - instruction text for YaGPT, varchar(1000)
- `timeout` - timeout value for YaGPT generation, integer
"""
