from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import format_dt

from custom_logger import Logger
from database_events import DatabaseEvents, EventExistsError
from permissions import require_admin

logger = Logger('gwaff.bot.event')


class EventCog(commands.GroupCog, group_name='event'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="create",
                          description="(Admin only) Creates a new event")
    @app_commands.describe(
        start_time='The start time of the event in the format "YYYY-MM-DD HH:MM"',
        end_time='The end time of the event in the format "YYYY-MM-DD HH:MM"',
        multiplier='The xp multiplier for the event')
    @require_admin
    async def create_event(self, interaction: discord.Interaction, start_time: str,
                           multiplier: float,
                           end_time: str = None):
        """
        Creates a new event.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
            if end_time:
                end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
        except ValueError:
            await interaction.followup.send(
                f"Invalid date format. Please use 'YYYY-MM-DD HH:MM'")
            return

        try:
            DatabaseEvents().create_event(start_time, end_time, multiplier)
        except EventExistsError:
            await interaction.followup.send(
                f"An event already exists. Please end the current event before creating a new one.")
            return

        if end_time:
            await interaction.followup.send(
                f"Event created from {format_dt(start_time)} to {format_dt(end_time)} with multiplier {multiplier}!")
        else:
            await interaction.followup.send(
                f"Event started at {format_dt(start_time)} with multiplier {multiplier}!")

    @app_commands.command(name="end",
                          description="(Admin only) Ends the current event")
    @app_commands.describe(end_time='The end time of the event in the format "YYYY-MM-DD HH:MM"')
    @require_admin
    async def end_event(self, interaction: discord.Interaction, end_time: str):
        """
        Ends the currently active event.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
        except ValueError:
            await interaction.followup.send(
                f"Invalid date format. Please use 'YYYY-MM-DD HH:MM'")
            return

        DatabaseEvents().end_event(end_time)
        await interaction.followup.send(f"Event ended at {format_dt(end_time)}!")


async def setup(bot: commands.Bot):
    """
    Sets up the EventCog and adds it to the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    cog = EventCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
