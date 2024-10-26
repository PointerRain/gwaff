from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands, utils
from discord.ext import commands

from bot import GwaffBot
from custom_logger import Logger
from database import DatabaseReader
from permissions import require_admin

logger = Logger('gwaff.bot.core')



COLLECTION_MAX_TIME: int = 120  # The time in minutes that must go by
                                # before collection is said to be stopped.
REDUCER_TIMEOUT: int = 60       # Time in seconds before the reducer process
                                # times out and is halted.


# class ReducerView(discord.ui.View):
#     def __init__(self, interaction: discord.Interaction):
#         super().__init__(timeout=REDUCER_TIMEOUT)
#         df = pd.read_csv("gwaff.csv", index_col=0)
#         self.reducer = Reducer(df)
#         self.started = False
#         self.interaction = interaction
#
#     async def on_timeout(self):
#         '''
#         Called when the view times out. This will deactivate the buttons.
#         '''
#         await self.interaction.edit_original_response(
#             content="Timed out"
#         )
#         await self.remove_view()
#         return
#
#     async def remove_view(self):
#         '''
#         Removes and deactivates the view.
#         '''
#         for child in self.children:
#             child.disabled = True
#         await self.interaction.edit_original_response(view=self)
#         self.stop()
#
#     @ui.button(label="Proceed", style=discord.ButtonStyle.danger)
#     async def button_one_callback(
#         self, interaction: discord.Interaction, button: ui.Button
#     ):
#         await interaction.response.defer()
#
#         if not self.started:
#             await self.interaction.edit_original_response(
#                 content=f"Processing..."
#             )
#
#             msg = self.reducer.reduce_cols()
#             if not msg:
#                 await self.interaction.edit_original_response(
#                     content=f"Something went wrong."
#                 )
#                 await self.remove_view()
#                 return
#             elif int(msg.split()[1]) <= 1:
#                 await self.interaction.edit_original_response(
#                     content=f"There are no columns to remove."
#                 )
#                 await self.remove_view()
#                 return
#
#             await self.interaction.edit_original_response(
#                 content=f"{msg}\nAre you really sure?"
#             )
#             self.started = True
#             return
#
#         else:
#             result = self.reducer.save()
#             if result:
#                 await self.interaction.edit_original_response(
#                     content=f"Saved the changes!"
#                 )
#             else:
#                 await self.interaction.edit_original_response(
#                     content=f"Something went wrong."
#                 )
#             await self.remove_view()
#             return
#
#     @ui.button(label="Cancel", style=discord.ButtonStyle.primary)
#     async def button_two_callback(
#         self, interaction: discord.Interaction, button: ui.Button
#     ):
#         await interaction.response.defer()
#         await self.interaction.edit_original_response(
#             content=f"Aborted!"
#         )
#         await self.remove_view()
#         return


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
        await interaction.followup.send(file=discord.File('gwaff.csv'))

    @app_commands.command(name="isalive",
                          description="When did I last collect data")
    @app_commands.describe(hidden='Hide from others in this server (default True)')
    async def is_alive(self, interaction: discord.Interaction,
                       hidden: bool = True):
        await interaction.response.defer(ephemeral=hidden)

        now = datetime.now()

        dbr = DatabaseReader()

        last = dbr.get_last_timestamp()
        last_str = utils.format_dt(last, 'R')

        prev_last = dbr.get_dates_in_range(now - timedelta(days=1))
        if len(prev_last) <= 1:
            prev_last_str = ""
        else:
            prev_last_str = f"(Before that {utils.format_dt(prev_last[-2], 'R')})\n"

        alive: str
        if (now - last).total_seconds() < 1.1 * COLLECTION_MAX_TIME * 60:
            alive = ""
        else:
            alive = "Collection has halted!"

        await interaction.followup.send(f"Data was last collected {last_str}\n"
                                        f"{prev_last_str}{alive}")

    # @app_commands.command(name="reduce", description="(Admin only) Clean up old datapoints")
    # @require_admin
    # async def reduce(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(
    #         "Do you want to run the reducer?", view=ReducerView(interaction),
    #         ephemeral=True
    #     )

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
        if self.bot.logging_channel:
            await self.bot.logging_channel.send("I have rebooted!")
        else:
            logger.warning(f"Could not find required channel")


async def setup(bot: GwaffBot):
    """
    Sets up the SpooncraftCog and adds it to the bot.

    Args:
        bot (GwaffBot): The bot instance.
    """
    cog = Core_Cog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
