import random
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from gwaff.bot import GwaffBot
from gwaff.custom_logger import Logger

logger = Logger('gwaff.bot.core')


class CoreCog(commands.Cog):
    def __init__(self, bot: GwaffBot):
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

    @app_commands.command(name="uptime", description="Get the bot's uptime")
    async def uptime(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Last rebooted: <t:{round(self.bot.reboot_time)}>"
            f" (<t:{round(self.bot.reboot_time)}:R>)",
            ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.reboot_time = datetime.now().timestamp()
        if random.randint(1, 50) == 1:
            await self.bot.send_message("Oopsie, I webooted uwu >_<")
        else:
            await self.bot.send_message("I have rebooted!")


async def setup(bot: GwaffBot):
    """
    Sets up the CoreCog and adds it to the bot.

    Args:
        bot (GwaffBot): The bot instance.
    """
    cog = CoreCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
