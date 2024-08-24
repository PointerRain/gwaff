from typing import Optional, Any, Callable

import discord
from discord import app_commands, utils
from discord.ext import commands

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from custom_logger import Logger
logger = Logger('gwaff.bot')


class GwaffBot(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any):
        discord.VoiceClient.warn_nacl = False

        intents = discord.Intents.default()
        super().__init__(*args,
                         intents=intents,
                         command_prefix="!",
                         activity=discord.Game(name='Gwaff'),
                         **kwargs)

        self.scheduler = AsyncIOScheduler()
        self.start_time = datetime.now()

        self.SERVER = 1118158249254985771
        self.CHANNEL = "gwaff"
        self.LOGGING_SERVER = 1077927097739247727
        self.LOGGING_CHANNEL = "testing"

        self.logging_server: discord.Guild
        self.logging_channel: discord.TextChannel
        self.server: discord.Guild = None
        self.channel: discord.TextChannel = None

        self.synced = False

    async def on_ready(self) -> None:
        if not self.synced:
            self.scheduler.start()

            if (server := self.get_guild(self.SERVER)) is not None:
                self.server = server
                logger.info(f"Found server")
                self.channel = discord.utils.get(
                    self.server.channels,
                    name=self.CHANNEL
                )
                if self.channel is not None and isinstance(self.channel, discord.TextChannel):
                    logger.info(f"Found logging channel")
                else:
                    logger.warning(f"Could not find logging channel #{self.bot.CHANNEL}")
                    self.channel = None
            else:
                logger.error(f"Unable to find server with id {str(self.SERVER)}")
                self.server = None
                self.channel = None

            if (server := self.get_guild(self.LOGGING_SERVER)) is not None:
                self.logging_server = server
                logger.info(f"Found logging server")
                self.logging_channel = discord.utils.get(
                    self.logging_server.channels,
                    name=self.LOGGING_CHANNEL
                )
                if self.logging_channel is not None and isinstance(self.logging_channel, discord.TextChannel):
                    logger.info(f"Found logging channel")
                else:
                    logger.warning(f"Could not find logging channel #{self.bot.LOGGING_CHANNEL}")
                    self.logging_channel = None
            else:
                logger.error(f"Unable to find logging server with id {str(self.LOGGING_SERVER)}")
                self.logging_server = None
                self.logging_channel = None

            server_finds = sum(bool(s)
                               for s in [self.server, self.logging_server])
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
        logger.info(f"User '{interaction.user.name}' "
                    f"used command '{command.name}' "
                    f"in guild '{interaction.guild.name}'")

    def schedule_task(self, func: Callable, *args: Any, **kwargs: Any):
        """Schedule a function to be run at a later time. A wrapper for apscheduler add_job."""
        self.scheduler.add_job(func, *args, **kwargs)
        # pass


cogs = [
    "core_cog",
    "plotter_cog",
    "stats_cog",
    "github_cog",
    "manage_cog"
]


async def run_the_bot(token) -> None:
    '''
    Runs the bot
    '''

    bot = GwaffBot()

    logger.info("Loading cogs")
    for cog in cogs:
        await bot.load_extension(cog)
        logger.info(f"- {cog}")
    logger.info("Loaded all cogs!")

    await bot.start(token)

if __name__ == '__main__':
    raise RuntimeError("Need to run through run_the_bot with the token!")
