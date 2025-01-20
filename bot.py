import os
from datetime import datetime
from logging import handlers
from typing import Any, Callable

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import utils
from discord.ext import commands

from custom_logger import Logger, BasicFormatter

logger = Logger('gwaff.bot')


class GwaffBot(commands.Bot):
    """
    A custom Discord bot class for Gwaff.

    Attributes:
        scheduler (AsyncIOScheduler): Scheduler for asynchronous tasks.
        start_time (datetime): The time when the bot was started.
        channel (discord.TextChannel): The main channel object.
        logging_channel (discord.TextChannel): The logging channel object.
        synced (bool): Indicates whether the bot has synced commands.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Initializes the GwaffBot instance.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.
        """
        discord.VoiceClient.warn_nacl = False

        intents = discord.Intents.default()
        super().__init__(*args,
                         intents=intents,
                         command_prefix="!",
                         activity=discord.Game(name='Gwaff'),
                         **kwargs)

        self.scheduler = AsyncIOScheduler()
        self.start_time = datetime.now()

        self.channel: discord.TextChannel = None
        self.logging_channel: discord.TextChannel = None

        self.synced = False

    async def find_channel(self, server_id: str, channel_name: str) -> None:
        """
        Finds a channel by name.

        Args:
            server_id (str | int): The server ID or name.
            channel_name (str): The channel name.

        Returns:
            discord.TextChannel | None: The channel object.
        """
        if server_id is None:
            logger.error(f"Server is not defined in environment variables")
            return None
        server = self.get_guild(int(server_id))
        if server is None:
            logger.error(f"Unable to find server with id {str(server_id)}")
            return None

        channel = discord.utils.get(server.channels, name=channel_name)
        if isinstance(channel, discord.TextChannel):
            logger.info(f"Found channel")
            return channel

        logger.warning(f"Could not find channel #{channel_name}")
        return None

    async def on_ready(self) -> None:
        """
        Event handler for when the bot is ready.
        Sets up logging, finds servers and channels, and syncs commands.
        """
        if not self.synced:
            self.scheduler.start()

            file_handler = handlers.TimedRotatingFileHandler(f'../discord.log',
                                                             when='midnight',
                                                             backupCount=2)
            basic_formatter = BasicFormatter(datefmt='%H:%M:%S')
            file_handler.setFormatter(basic_formatter)

            utils.setup_logging(handler=file_handler, formatter=basic_formatter, root=False)

            self.channel = await self.find_channel(os.environ.get('SERVER'),
                                                   os.environ.get('CHANNEL'))
            self.logging_channel = await self.find_channel(os.environ.get('LOGGING_SERVER'),
                                                           os.environ.get('LOGGING_CHANNEL'))

            server_finds = sum(bool(s)
                               for s in [self.channel, self.logging_channel])
            if server_finds == 0:
                logger.error(f"Found {server_finds} of 2 servers")
            elif server_finds == 1:
                logger.warning(f"Found {server_finds} of 2 servers")
            else:
                logger.info(f"Found {server_finds} of 2 servers")

            await self.tree.sync()
            for server in self.guilds:
                await self.tree.sync(guild=discord.Object(id=server.id))
                logger.info("- " + server.name)
            self.synced = True
        logger.info("Ready!")

    async def on_app_command_completion(self, interaction, command):
        """
        Event handler for when an application command is completed.

        Args:
            interaction (discord.Interaction): The interaction that triggered the command.
            command (discord.ApplicationCommand): The command that was completed.
        """
        logger.info(f"User '{interaction.user.name}' "
                    f"used command '{command.name}' "
                    f"in guild '{interaction.guild.name}'")

    def schedule_task(self, func: Callable, *args: Any, **kwargs: Any):
        """
        Schedule a function to be run at a later time. A wrapper for apscheduler add_job.

        Args:
            func (Callable): The function to schedule.
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.
        """
        self.scheduler.add_job(func,
                               trigger="cron",
                               timezone="Australia/Brisbane",
                               misfire_grace_time=599,
                               coalesce=True,
                               max_instances=1,
                               *args,
                               **kwargs)


cogs = [
    "core_cog",
    "plotter_cog",
    "stats_cog",
    "github_cog",
    "manage_cog",
    "spooncraft_cog",
    "event_cog"
]


async def run_the_bot(token) -> None:
    """
    Runs the bot.

    Args:
        token (str): The token to authenticate the bot.
    """
    bot = GwaffBot()

    logger.info("Loading cogs")
    for cog in cogs:
        await bot.load_extension(f"{cog}")
        logger.info(f"- {cog}")
    logger.info("Loaded all cogs!")

    await bot.start(token)


if __name__ == '__main__':
    raise RuntimeError("Need to run through run_the_bot with the token!")
