import os
from functools import wraps
from typing import Callable, Any, Coroutine

import discord
from discord import Interaction
from discord.ext import commands
from discord.ext.commands import Cog

os.environ.get('')
ADMIN_LIST: set[int] = {int(owner_id)} if (
    owner_id := os.environ.get('OWNER_ID')) else set()  # Set of discord ids of admin users.


def require_admin(func) -> Callable[[Cog, Interaction, tuple, dict[str, Any]], Coroutine[Any, Any, None]]:
    """
    Restricts command usage to admin users only.
    """

    @wraps(func)
    async def wrapper(
            cog: commands.Cog,
            interaction: discord.Interaction,
            *args,
            **kwargs
    ):
        if int(interaction.user.id) in ADMIN_LIST:
            await func(cog, interaction, *args, **kwargs)
            return
        await interaction.response.send_message(":no_entry: You can't use this command", ephemeral=True)

    return wrapper
