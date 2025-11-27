from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import format_dt

from gwaff.cogs.permissions import require_admin
from gwaff.custom_logger import Logger
from gwaff.database.db_events import DatabaseEvents, EventExistsError

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
    async def create_event(self, interaction: discord.Interaction,
                           start_time: str,
                           multiplier: float,
                           end_time: str | None = None):
        """
        Creates a new event.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
            if end_time:
                end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
            else:
                end_datetime = None
        except ValueError:
            await interaction.followup.send(
                f"Invalid date format. Please use 'YYYY-MM-DD HH:MM'")
            return

        try:
            DatabaseEvents().create_event(start_datetime, end_datetime, multiplier)
        except EventExistsError:
            await interaction.followup.send(
                f"An event already exists. Please end the current event before creating a new one.")
            return

        if end_time is not None:
            assert end_datetime is not None
            await interaction.followup.send(
                f"Event created from {format_dt(start_datetime)} to {format_dt(end_datetime)} with multiplier {multiplier}!")
        else:
            await interaction.followup.send(
                f"Event started at {format_dt(start_datetime)} with multiplier {multiplier}!")

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
            end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
        except ValueError:
            await interaction.followup.send(
                f"Invalid date format. Please use 'YYYY-MM-DD HH:MM'")
            return

        DatabaseEvents().end_event(end_datetime)
        await interaction.followup.send(f"Event ended at {format_dt(end_datetime)}!")

    @app_commands.command(name="list",
                          description="List all xp events")
    async def list_events(self, interaction: discord.Interaction):
        """
        Lists all XP events.
        """
        await interaction.response.defer(ephemeral=True)

        events = DatabaseEvents().get_events()
        if not events:
            await interaction.followup.send("No events found.")
            return

        event_lines = []
        for event in events:
            start_str = format_dt(event.start_time)
            end_str = format_dt(event.end_time) if event.end_time else "Ongoing"
            event_lines.append(
                f"ID: {event.id:02} | Start: {start_str} | End: {end_str} | Multiplier: {event.multiplier}")

        event_message = "\n".join(event_lines)
        await interaction.followup.send(f"**XP Events:**\n{event_message}")


async def setup(bot: commands.Bot):
    """
    Sets up the EventCog and adds it to the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    cog = EventCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
