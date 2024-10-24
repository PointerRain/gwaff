from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from gwaff.custom_logger import Logger
logger = Logger('gwaff.bot.cogs')

class ManageCogs(commands.Cog):
    """
    Note that most of these commands can make the bot load files to execute. Care should be made to ensure only entrusted users have access.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="managecogs")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def manage_cogs(
        self, interaction: discord.Interaction,
        action: Literal["load", "unload", "reload"],
        cog: str,
    ):
        """
        Trys to unload a cog (i.e. python file).
        Note that most of these commands can make the bot load files to execute. Care should be made to ensure only entrusted users have access.
        """
        try:
            if action == "load":
                await self.bot.load_extension(f"{cog}")
            elif action == "unload":
                await self.bot.unload_extension(f"{cog}")
            elif action == "reload":
                await self.bot.reload_extension(f"{cog}")
            else:
                raise Exception("Unknown Operation")
        except Exception as error:
            # Many errors can be caught during loading/unloading/reloading the bot, so it would be painful to separate by exception type
            await interaction.response.send_message(
                f"Error occured {action}ing {cog}: {error}"
            )
            logger.error(f"Error occured {action}ing {cog}: {error}")
            return
        await interaction.response.send_message(f"Successfully {action}ed {cog}")
        logger.info(f"Successfully {action}ed {cog}")
        await self.bot.tree.sync()


async def setup(bot: commands.Bot):
    await bot.add_cog(ManageCogs(bot))