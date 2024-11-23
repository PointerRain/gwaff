import discord
import requests
from discord import app_commands
from discord.ext import commands

from bot import GwaffBot
from custom_logger import Logger
from database_events import DatabaseEvents
from permissions import require_admin

logger = Logger('gwaff.bot.event')


class SpooncraftCog(commands.GroupCog, group_name='event'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="create",
                          description="(Admin only) Creates a new event")
    @app_commands.describe(hidden='Hide from others in this server (default True)')
    @require_admin
    def create_event(self, interaction: discord.Interaction, start_time: str, end_time: str = None,
                     multiplier: float = None):
        """
        Creates a new event.
        """
        start_time = start_time.replace('T', ' ')
        if end_time:
            end_time = end_time.replace('T', ' ')

        DatabaseEvents().create_event(start_time, end_time, multiplier)

        interaction.response.send_message(f"Event created!")
