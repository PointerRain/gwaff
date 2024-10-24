import discord
from discord import app_commands
from discord.ext import commands

from gwaff.custom_logger import Logger
from gwaff.database_mc import DatabaseMinecraft
from gwaff.bot.bot import GwaffBot

logger = Logger('gwaff.bot.spooncraft')

from gwaff.permissions import require_admin


class SpooncraftCog(commands.GroupCog, group_name='spooncraft'):

    def __init__(self, bot: GwaffBot):
        """
        Initialises the SpooncraftCog with the bot instance and schedules tasks.

        Args:
            bot (GwaffBot): The bot instance.
        """
        self.bot = bot

        # Upload the data every day at midnight
        self.bot.schedule_task(
            self.upload,
            trigger="cron",
            hour=0,
            timezone="Australia/Brisbane"
        )

        # Update names every month
        self.bot.schedule_task(
            self.update_names,
            trigger="cron",
            hour=23,
            timezone="Australia/Brisbane",
            day='last'
        )

    async def upload(self):
        """
        Asynchronously uploads Spooncraft data and logs the process.
        """
        logger.info("Starting upload")
        if self.bot.logging_channel:
            await self.bot.logging_channel.send("Upload SC data here!")
        else:
            logger.warning(f"Could not find required channel")
        logger.info("Upload was not completed successfully")

    async def update_names(self):
        """
        Asynchronously updates Minecraft names and logs the process.
        """
        # TODO: Fix blocking
        logger.info("Starting update")
        if self.bot.logging_channel:
            await self.bot.logging_channel.send("Updating names now!")
        else:
            logger.warning(f"Could not find required channel")
        dbm = DatabaseMinecraft()
        success, total = await dbm.update_all_mc_names()
        if self.bot.logging_channel:
            await self.bot.logging_channel.send(
                f"Finished updating names with {total - success} fails out of {total}!")
        logger.info(f"Finished updating names with {total - success} fails out of {total}!")

    @app_commands.command(name="upload",
                          description="(Admin only) Upload the Spooncraft data")
    @require_admin
    async def command_upload(self, interaction: discord.Interaction):
        """
        Command to upload Spooncraft data.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer(ephemeral=True)
        await self.upload()
        await interaction.followup.send("No such luck")

    @app_commands.command(name="updateall",
                          description="(Admin only) Update Spooncraft MC names")
    @require_admin
    async def command_updateall(self, interaction: discord.Interaction):
        """
        Command to update all Minecraft names.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.followup.send("Starting the update")
        dbm = DatabaseMinecraft()
        success, total = await dbm.update_all_mc_names()
        await msg.edit(
            content=f"Finished updating names with {total - success} fails out of {total}!")

    @app_commands.command(name="add",
                          description="(Admin only) Add a Spooncraft player")
    @require_admin
    async def command_add(self, interaction: discord.Interaction,
                          member: discord.User,
                          uuid: str,
                          name: str = None):
        """
        Command to add a Spooncraft player to the database.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.User): The Discord user to add.
            uuid (str): The UUID of the Minecraft player.
            name (str, optional): The name of the Minecraft player. Defaults to None.
        """
        await interaction.response.defer(ephemeral=True)
        dbm = DatabaseMinecraft()
        dbm.add_user(member.id, uuid, name)
        dbm.commit()
        if name:
            await interaction.followup.send(
                f"Added user {member.mention} with UUID {uuid} and name {name}")
        else:
            await interaction.followup.send(f"Added user {member.mention} with UUID {uuid}")


async def setup(bot: GwaffBot):
    """
    Sets up the SpooncraftCog and adds it to the bot.

    Args:
        bot (GwaffBot): The bot instance.
    """
    cog = SpooncraftCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
