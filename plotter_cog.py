import os
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from bot import GwaffBot
from custom_logger import Logger
from growth import Growth
from utils import resolve_member

logger = Logger('gwaff.bot.plot')

GRAPH_MAX_DAYS: int = int(os.environ.get("GRAPH_MAX_DAYS", 365))
GRAPH_DEFAULT_DAYS: int = int(os.environ.get("GRAPH_DEFAULT_DAYS", 7))
GRAPH_MAX_USERS: int = int(os.environ.get("GRAPH_MAX_USERS", 30))
GRAPH_DEFAULT_USERS: int = int(os.environ.get("GRAPH_DEFAULT_USERS", 15))


def growth(days: int = GRAPH_DEFAULT_DAYS,
           count: int = GRAPH_DEFAULT_USERS,
           member: discord.User = None,
           title: str = "Top chatters XP growth",
           special: bool = False,
           compare: discord.User = None) -> str:
    """
    Plots and saves a growth plot (aka gwaff)
    """
    if days >= GRAPH_MAX_DAYS:
        days = GRAPH_MAX_DAYS
    elif days <= 0:
        days = 0

    plot = Growth(start_date=datetime.now() - timedelta(days=days),
                  special=special,
                  title=title)
    if member is None:
        include = None
    else:
        include = {member.id}
    if compare is not None:
        include = {member.id, compare.id}
        plot.title = f"Comparing growth over the last {round(days)} days"

    plot.draw(limit=count, include=include)
    plot.draw_events()
    plot.annotate()
    plot.configure()

    path = plot.save(name)
    plot.close()

    return path


class PlotterCog(commands.Cog):
    def __init__(self, bot: GwaffBot):
        self.bot = bot

        self.growth_ctxmenu = app_commands.ContextMenu(
            name='Growth',
            callback=self.growth_ctx
        )
        self.bot.tree.add_command(self.growth_ctxmenu)

    async def regular(self):
        try:
            growth(name='regular')
        except Exception as e:
            logger.error("Regular graph plotting failed!")
            await self.bot.send_message("Regular graph plotting failed!", log=True)

    @app_commands.command(name="gwaff",
                          description="Plots top users growth")
    @app_commands.describe(
        days=f'How many days to plot (default {GRAPH_DEFAULT_DAYS})',
        count=f'How many users to plot (default {GRAPH_DEFAULT_USERS})',
        hidden='Hide from others in this server (default False)')
    async def plot_gwaff(self, interaction: discord.Interaction,
                         days: app_commands.Range[float, 1, GRAPH_MAX_DAYS] = GRAPH_DEFAULT_DAYS,
                         count: app_commands.Range[int, 1, GRAPH_MAX_USERS] = GRAPH_DEFAULT_USERS,
                         hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)

        title: str
        if days == GRAPH_DEFAULT_DAYS:
            title = "Top chatters XP growth"
        else:
            title = f"Top chatters XP over the last {round(days)} days"
        path = growth(days=days, count=count, title=title, special=True)
        await interaction.followup.send(file=discord.File(path))

    @app_commands.command(name="growth",
                          description="Plots a specific member's growth")
    @app_commands.describe(member="The member plot (default you)",
                           days="How many days to plot (default 7)",
                           compare="A second user to show",
                           hidden="Hide from others in this server (default False)")
    async def plot_growth(self, interaction: discord.Interaction,
                          member: discord.User = None,
                          days: app_commands.Range[int, 1, GRAPH_MAX_DAYS] = GRAPH_DEFAULT_DAYS,
                          compare: discord.User = None,
                          hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)
        member = resolve_member(interaction, member)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return

        co_member: discord.User | None = None
        if compare:
            co_member = resolve_member(None, compare)
            if co_member is False:
                await interaction.followup.send(":bust_in_silhouette: "
                                                "The compared person is not in "
                                                "the server or hasn't reached "
                                                "level 15")
                return

        try:
            path = growth(days=days, member=member, count=1,
                          title=f"{member.name}'s growth over the last {round(days)} days",
                          compare=co_member)
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return
        await interaction.followup.send(file=discord.File(path))

    async def growth_ctx(self, interaction: discord.Interaction,
                         member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        member = resolve_member(interaction, member)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return
        try:
            path = growth(days=GRAPH_DEFAULT_DAYS, member=member, count=1,
                          title=f"{member.name}'s growth over the last {round(GRAPH_DEFAULT_DAYS)} days")
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return
        await interaction.followup.send(file=discord.File(path))


async def setup(bot: GwaffBot):
    cog = PlotterCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
