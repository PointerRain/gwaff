import discord
from discord import app_commands, utils
from discord.ext import commands
from datetime import datetime, timedelta

from utils import resolve_member
from growth import Growth
from custom_logger import Logger
logger = Logger('gwaff.bot.plot')


GRAPH_MAX_DAYS: int = 365       # The maximum number of days that can be plotted
GRAPH_DEFAULT_DAYS: int = 7     # The default number of days to be plot
GRAPH_MAX_USERS: int = 30       # The maximum number of users that can be plotted
GRAPH_DEFAULT_USERS: int = 15   # The default number of users to be plot


def growth(days: int = GRAPH_DEFAULT_DAYS,
           count: int = GRAPH_DEFAULT_USERS,
           member: discord.User = None,
           title: str = "Top chatters XP growth",
           special: bool = False,
           compare: discord.User = None) -> None:
    '''
    Plots and saves a growth plot (aka gwaff)

    '''
    if days >= GRAPH_MAX_DAYS:
        days = GRAPH_MAX_DAYS
    elif days <= 0:
        days = 0

    plot = Growth(start_date=datetime.now() - timedelta(days=days),
                  special=special,
                  title=title)
    if member is None:
        include = None
        count = count
    else:
        include = [member.id]
        count = 1
    if compare is not None:
        include = [member.id, compare.id]
        count = 2
        plot.title = f"Comparing growth over the last {round(days)} days"
    plot.draw(max_count=count, include=include)
    plot.annotate()
    plot.configure()

    plot.save()
    plot.close()


class Plotter_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.growth_ctxmenu = app_commands.ContextMenu(
            name='Growth',
            callback=self.growth_ctx
        )
        self.bot.tree.add_command(self.growth_ctxmenu)

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
        growth(days=days, count=count, title=title, special=True)
        await interaction.followup.send(file=discord.File('out.png'))

    @app_commands.command(name="growth",
                          description="Plots a specific member's growth")
    @app_commands.describe(member="The member plot (default you)",
                           days="How many days to plot (default 7)",
                           compare="A second user to show",
                           hidden="Hide from others in this server (default False)")
    async def plot_growth(self, interaction: discord.Interaction,
                          member: discord.User = None,
                          days: app_commands.Range[float, 1, GRAPH_MAX_DAYS] = GRAPH_DEFAULT_DAYS,
                          compare: discord.User = None,
                          hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)
        member = resolve_member(interaction, member)
        if member is False:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person in not in the server "
                                            "or hasn't reached level 15")
            return

        co_member: discord.User = None
        if compare:
            co_member = resolve_member(None, compare)
            if co_member is False:
                await interaction.followup.send(":bust_in_silhouette: "
                                                "The compared person is not in "
                                                "the server or hasn't reached "
                                                "level 15")
                return

        try:
            growth(days=days, member=member, count=1,
                   title=f"{member.name}'s growth over the last {round(days)} days",
                   compare=co_member)
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return
        await interaction.followup.send(file=discord.File('out.png'))

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
            growth(days=GRAPH_DEFAULT_DAYS, member=member, count=1,
                   title=f"{member.name}'s growth over the last {round(days)} days")
        except IndexError:
            await interaction.followup.send(":bust_in_silhouette: "
                                            "That person has not been online "
                                            "recently enough")
            return
        await interaction.followup.send(file=discord.File('out.png'))


async def setup(bot: commands.Bot):
    cog = Plotter_Cog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
