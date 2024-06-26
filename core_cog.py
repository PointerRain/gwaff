import discord
from discord import app_commands, utils
from discord.ext import commands

from datetime import datetime, timedelta, timezone
import pandas as pd
from custom_logger import Logger
logger = Logger('gwaff.bot.core')

from permissions import require_admin
from plotter import Plotter


COLLECTION_MAX_TIME: int = 120      # The maximum length of time that must go by
                                    # before collection is said to be stopped.

class Core_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="data",
                  description="(Admin only) Gets the entire gwaff data as a csv")
    @app_commands.describe(hidden='Hide from others in this server (default True)')
    @require_admin
    async def send_data(self, interaction: discord.Interaction,
                        hidden: bool = True):
        await interaction.response.defer(ephemeral=hidden)
        await interaction.followup.send(file=discord.File('gwaff.csv'), ephemeral=hidden)


    @app_commands.command(name="last",
                  description="(Admin only) Sends the last plot")
    @app_commands.describe(hidden='Hide from others in this server (default False)')
    @require_admin
    async def send_data(self, interaction: discord.Interaction,
                        hidden: bool = False):
        await interaction.response.defer(ephemeral=hidden)
        await interaction.followup.send(file=discord.File('out.png'), ephemeral=hidden)


    @app_commands.command(name="isalive",
                  description="When did I last collect data")
    @app_commands.describe(hidden='Hide from others in this server (default True)')
    async def is_alive(self, interaction: discord.Interaction,
                       hidden: bool = True):
        await interaction.response.defer(ephemeral=hidden)

        now = datetime.now()

        data = pd.read_csv("gwaff.csv", index_col=0)
        plot = Plotter(data)

        last = plot.dates[-1]
        last = datetime.fromisoformat(last)
        laststr = utils.format_dt(last, 'R')

        prevlast = plot.dates[-2]
        prevlast = datetime.fromisoformat(prevlast)
        prevlaststr = utils.format_dt(prevlast, 'R')

        alive: str;
        if (now - last).total_seconds() < 1.1 * COLLECTION_MAX_TIME*60:
            alive = ""
        else:
            alive = "Collection has halted!"
        await interaction.followup.send(f"Data was last collected {laststr}\n"
                                        f"(Before that {prevlaststr})\n{alive}")


    '''
    # @app_commands.command(name="reduce")
    # async def reduce(interaction: discord.Interaction):
    #     if interaction.user.id in [344731282095472641]:
    #         await interaction.response.defer(ephemeral=True)
    #         start_size = 0
    #         reduce()
    #         end_size = 0
    #         await interaction.followup.send(f"Reduced filesize by "
    #                                         f"{end_size-start_size}!")
    #     else:
    #         await interaction.followup.send(":no_entry: You can't use this command",
    #                                         ephemeral=True)
    '''


    @app_commands.command(name="ping", description="Pong!")
    async def ping(self, interaction: discord.Interaction):
        now = datetime.now(timezone.utc)
        msgtime = interaction.created_at
        ping = (now - msgtime).total_seconds() * 2000.0
        logger.info(f"Ping: {ping}")
        await interaction.response.send_message(f"Pong!\n{round(ping)} ms",
                                                ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = discord.utils.get(
            self.bot.server.channels, name=self.bot.CHANNEL_NAME
        )

        if isinstance(self.channel, discord.TextChannel):
            await self.channel.send("I have rebooted!")
        else:
            logging.warning("Could not find required channel #{self.bot.CHANNEL_NAME}")

async def setup(bot: commands.Bot):
    cog = Core_Cog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)