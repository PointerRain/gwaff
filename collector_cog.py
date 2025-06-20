import os
from datetime import datetime, timedelta

import discord
from discord import app_commands, utils, ui
from discord.ext import commands

from bot import GwaffBot
from collector import record_data, update_profiles
from custom_logger import Logger
from database import DatabaseReader
from permissions import require_admin
from reducer import DatabaseReducer

logger = Logger('gwaff.bot.collector')

COLLECTION_MAX_TIME: int = int(os.environ.get("MAX_SEPARATION", 120))
REDUCER_TIMEOUT: int = 60  # Time in seconds before the reducer process times out and is halted.

COLLECTION_SMALL: int = int(os.environ.get("COLLECTION_SMALL", 2))
COLLECTION_LARGE: int = int(os.environ.get("COLLECTION_LARGE", 6))
COLLECTION_LARGEST: int = int(os.environ.get("COLLECTION_LARGEST", 10))


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
        """
        Collects data from a small range of pages.
        """
        logger.info("Starting short data collection")
        try:
            record_data(pages=range(1, COLLECTION_SMALL))
        except Exception as e:
            self.bot.send_message(f"Data collection failed! {str(e)}")

    async def collect_long(self):
        """
        Collects data from a larger range of pages.
        """
        logger.info("Starting long data collection")
        try:
            record_data(pages=range(1, COLLECTION_LARGE))
        except Exception as e:
            self.bot.send_message(f"Data collection failed! {str(e)}")

    async def update_profiles(self):
        """
        Updates the profiles of all users.
        """
        logger.info("Starting profile update")
        try:
            update_profiles()
        except Exception as e:
            self.bot.send_message(f"Data collection failed! {str(e)}")


    async def reduce():
        """
        Reduces the database by removing old records.
        WARNING: This is a destructive operation and cannot be undone. It does not ask for confirmation.
        """
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
