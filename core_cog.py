from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from bot import GwaffBot
from custom_logger import Logger

logger = Logger('gwaff.bot.core')


class Core_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Pong!")
    async def ping(self, interaction: discord.Interaction):
        now = datetime.now(timezone.utc)
        msgtime = interaction.created_at
        ping = (now - msgtime).total_seconds() * 2000.0
        logger.info(f"Ping: {ping}")
        await interaction.response.send_message(f"Pong!\n{round(ping)} ms",
                                                ephemeral=True)

    @app_commands.command(name="jobs", description="List all scheduled jobs")
    async def list_jobs(self, interaction: discord.Interaction):
        jobs = self.bot.scheduler.get_jobs()
        job_str = "\n".join([f"{job.name:>30}: next run at {job.next_run_time}" for job in jobs])
        await interaction.response.send_message(f"```{job_str}```", ephemeral=True)

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
