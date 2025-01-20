from datetime import datetime, timedelta

import discord
from discord import app_commands, utils, ui
from discord.ext import commands

from bot import GwaffBot
from custom_logger import Logger
from database import DatabaseReader
from permissions import require_admin

from collector import record_data, update_profiles
from reducer import DatabaseReducer

logger = Logger('gwaff.bot.collector')

COLLECTION_MAX_TIME: int = 120  # The time in minutes that must go by before collection is said to be stopped.
REDUCER_TIMEOUT: int = 60  # Time in seconds before the reducer process times out and is halted.

COLLECTION_SMALL: int = 2  # Collect data from up to this page every collection event
COLLECTION_LARGE: int = 6  # Collect data from up to this page every second collection event
COLLECTION_LARGEST: int = 10  # Update names up to this page when updating names


class ReducerView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=REDUCER_TIMEOUT)
        self.reducer = DatabaseReducer()
        self.started = False
        self.interaction = interaction

    async def on_timeout(self):
        """
        Called when the view times out. This will deactivate the buttons.
        """
        await self.interaction.edit_original_response(
            content="Timed out"
        )
        await self.remove_view()
        return

    async def remove_view(self):
        """
        Removes and deactivates the view.
        """
        for child in self.children:
            child.disabled = True
        await self.interaction.edit_original_response(view=self)
        self.stop()

    @ui.button(label="Proceed", style=discord.ButtonStyle.danger)
    async def button_one_callback(
            self, interaction: discord.Interaction, button: ui.Button
    ):
        await interaction.response.defer()

        if not self.started:
            await self.interaction.edit_original_response(
                content=f"Processing..."
            )
            count = self.reducer.reduce()
            if not count:
                await self.interaction.edit_original_response(
                    content=f"Something went wrong."
                )
                await self.remove_view()
                return
            elif count <= 1:
                await self.interaction.edit_original_response(
                    content=f"There are no columns to remove."
                )
                await self.remove_view()
                return

            await self.interaction.edit_original_response(
                content=f"Deleting {count} records\nAre you really sure?"
            )
            self.started = True
            return

        else:
            self.reducer.commit()
            await self.interaction.edit_original_response(
                content=f"Saved the changes!"
            )
            await self.remove_view()
            return

    @ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def button_two_callback(
            self, interaction: discord.Interaction, button: ui.Button
    ):
        await interaction.response.defer()
        self.reducer.rollback()
        await self.interaction.edit_original_response(
            content=f"Aborted!"
        )
        await self.remove_view()
        return


class CollectorCog(commands.GroupCog, group_name='collector'):
    def __init__(self, bot: GwaffBot):
        self.bot = bot

        self.bot.schedule_task(
            self.collect_short,
            hour='0-23/2',
            minute=0
        )
        self.bot.schedule_task(
            self.collect_long,
            hour='1-23/2',
            minute=0
        )
        self.bot.schedule_task(
            self.update_profiles,
            hour=0,
            minute=10
        )

    # @app_commands.command(name="data",
    #                       description="(Admin only) Gets the entire gwaff data as a csv")
    # @app_commands.describe(hidden='Hide from others in this server (default True)')
    # @require_admin
    # async def send_data(self, interaction: discord.Interaction,
    #                     hidden: bool = True):
    #     await interaction.response.defer(ephemeral=hidden)
    #     await interaction.followup.send(file=discord.File('gwaff.db'))

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

    @app_commands.command(name="reduce", description="(Admin only) Clean up old datapoints")
    @require_admin
    async def reducer_ui(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Do you want to run the reducer?", view=ReducerView(interaction),
            ephemeral=True
        )

    async def collect_short(self):
        logger.info("Starting short data collection")
        record_data(pages=range(1, COLLECTION_SMALL))

    async def collect_long(self):
        logger.info("Starting long data collection")
        record_data(pages=range(1, COLLECTION_LARGE))

    async def update_profiles(self):
        logger.info("Starting profile update")
        update_profiles()

    async def reduce(self):
        logger.info("Starting data reduction")
        dr = DatabaseReducer()
        count = dr.reduce()
        if count > 1:
            logger.info(f"Reduced {count} records")


async def setup(bot: GwaffBot):
    """
    Sets up the CollectorCog and adds it to the bot.

    Args:
        bot (GwaffBot): The bot instance.
    """
    cog = CollectorCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
