from typing import Optional, Any, Callable
from functools import wraps

import discord
from discord import app_commands
from discord.ext import commands

ADMIN_LIST: list[int] = [344731282095472641]


def require_admin(func: app_commands.AppCommand):
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
