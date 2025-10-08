from typing import Any

import discord
import requests
from discord import app_commands
from discord.ext import commands

from gwaff.bot import GwaffBot
from gwaff.custom_logger import Logger
from gwaff.database.db_spooncraft import DatabaseMinecraft
from gwaff.cogs.permissions import require_admin

logger = Logger('gwaff.bot.spooncraft')


def update_data(url: str, new_data: dict[str, Any]) -> bool:
    """
    Updates the data on the Spooncraft API.

    Args:
        url (str): URL to upload the data to.
        new_data (dict): The new data to update.
    """
    headers = {'Content-Type': 'application/json', "User-Agent": "Mozilla/5.0"}
    response = requests.post(url, json=new_data, headers=headers)
    if response.status_code == 200:
        logger.info(f"Data updated successfully: {response.json()}")
        return True
    else:
        logger.info(f"Failed to update data: {response.status_code, response.text}")
        return False


class SpooncraftCog(commands.GroupCog, group_name='spooncraft'):

    def __init__(self, bot: GwaffBot):
        """
        Initialises the SpooncraftCog with the bot instance and schedules tasks.

        Args:
            bot (GwaffBot): The bot instance.
        """
        self.bot: GwaffBot = bot

        # Update names every month
        self.bot.schedule_task(
            self.update_names,
            hour=0,
            minute=20,
            day='last'
        )

        # Upload the data every day at midnight
        self.bot.schedule_task(
            self.upload,
            hour=0,
            minute=30
        )

    async def upload(self) -> bool:
        """
        Asynchronously uploads Spooncraft data and logs the process.
        """
        dbm = DatabaseMinecraft()
        logger.info("Starting upload")

        data = dbm.to_json()
        result = update_data("https://gwaff.uqcloud.net/api/spooncraft", data)
        if result:
            logger.info("Upload completed successfully!")
        else:
            logger.warning(f"Upload failed!")
            await self.bot.send_message("SC data upload failed", log=True)

        data = {
            'version': 2,
            'mappings': dbm.to_json_dict(),
            'whitelist': ['mc.thatmumbojumbo.com', 'creative.thatmumbojumbo.com', 'play.thatmumbojumbo.com',
                          '173.233.142.94', '173.233.142.2'],
            'blacklist': ['uhc.thatmumbojumbo.com', '173.233.142.10', 'cytooxien.de', 'cytooxien.net']
        }
        result = update_data("https://gwaff.uqcloud.net/scnicknamer/", data)
        if result:
            logger.info("Upload completed successfully!")
        else:
            logger.warning(f"Upload failed!")
            await self.bot.send_message("SC data upload failed", log=True)

        return True

    async def update_names(self) -> tuple[int, int]:
        """
        Asynchronously updates Minecraft names.
        """
        # TODO: Fix blocking
        logger.info("Starting update")
        await self.bot.send_message("Updating names now", log=True)

        dbm = DatabaseMinecraft()
        success, total = await dbm.update_all_mc_names()
        await self.bot.send_message(
            f"Finished updating names with {total - success} fails out of {total}!",
            log=True)
        logger.info(f"Finished updating names with {total - success} fails out of {total}!")
        return success, total

    @app_commands.command(name="upload",
                          description="(Admin only) Upload the Spooncraft data")
    @require_admin
    async def command_upload(self, interaction: discord.Interaction) -> None:
        """
        Command to upload Spooncraft data.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer(ephemeral=True)
        # dbm: DatabaseMinecraft = DatabaseMinecraft()
        result = await self.upload()
        if result:
            await interaction.followup.send("Data uploaded successfully!")
        else:
            await interaction.followup.send("Data upload failed!")

    # @app_commands.command(name="updateall",
    #                       description="(Admin only) Update Spooncraft MC names")
    # @require_admin
    # async def command_update_names(self, interaction: discord.Interaction) -> None:
    #     """
    #     Command to update all Minecraft names.
    #
    #     Args:
    #         interaction (discord.Interaction): The interaction object.
    #     """
    #     # TODO: Fix blocking
    #     await interaction.response.defer(ephemeral=True)
    #     success, total = await self.update_names()
    #     await interaction.followup.send(f"Finished updating names with {total - success} fails out of {total}!")

    @app_commands.command(name="add",
                          description="(Admin only) Add a Spooncraft player")
    @require_admin
    async def command_add(self, interaction: discord.Interaction,
                          member: discord.User,
                          uuid: str,
                          name: str = None) -> None:
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
                f"Added user {member.mention} with UUID `{uuid}` and name `{name}`")
        else:
            await interaction.followup.send(f"Added user {member.mention} with UUID `{uuid}`")


async def setup(bot: GwaffBot) -> None:
    """
    Sets up the SpooncraftCog and adds it to the bot.

    Args:
        bot (GwaffBot): The bot instance.
    """
    cog = SpooncraftCog(bot)
    await bot.add_cog(cog, guilds=bot.guilds)
