import discord
from discord import app_commands, utils
from discord.ext import commands

import logging

from permissions import require_admin

class Github_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.schedule_task(
            self.upload, trigger="cron", hour=1, timezone="Australia/Brisbane"
        )

        self.channel = None

    async def upload(self):
        if isinstance(self.channel, discord.TextChannel):
            await self.channel.send("Hello!")
        else:
            logging.warning(f"Could not find required channel #{self.bot.CHANNEL_NAME}")

    @app_commands.command(name="upload",
                          description="(Admin only) Upload the data to github")
    async def command_upload(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.upload()
        await interaction.followup.send("No such luck")

    @app_commands.command(name="update",
                          description="(Admin only) Update the bot from github")
    async def update(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("No such luck")

    async def scheduled_upload(self):
        await self.upload()

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = discord.utils.get(
            self.bot.server.channels, name=self.bot.CHANNEL_NAME
        )

async def setup(bot: commands.Bot):
    cog = Github_Cog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)

