from typing import Optional, Any, Callable
from functools import wraps

import discord

ADMIN_LIST: list[int] = [344731282095472641]


def require_admin(func: Callable):
    @wraps(func)
    async def wrapper(
        interaction: discord.Interaction,
        *args,
        hidden: bool = True,
        **kwargs
    ):
        if int(interaction.user.id) in ADMIN_LIST:
            await interaction.response.defer(ephemeral=hidden)
            await func(interaction, *args, **kwargs)
            return
        await interaction.response.send_message(":no_entry: You can't use this command", ephemeral=True)
    return wrapper
