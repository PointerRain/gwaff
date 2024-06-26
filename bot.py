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

        self.LOGGING_SERVER = 1118158249254985771
        self.CHANNEL_NAME = "gwaff"

        self.server: discord.Guild

        self.synced = False
        self.servers = []

    async def on_ready(self) -> None:
        self.scheduler.start()

        if (server := self.get_guild(self.LOGGING_SERVER)) is None:
            raise RuntimeError(f"[BOT] Unable to find server with id {str(self.LOGGING_SERVER)}")
        self.server = server
        logging.info("Got server!")

        if not self.synced:
            await self.tree.sync()
            for server in self.guilds:
                await self.tree.sync(guild=discord.Object(id=server.id))
                logger.info("- " + server.name)
            self.synced = True
        logger.info("Ready!")

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
