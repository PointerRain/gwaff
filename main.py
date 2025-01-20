import os
import asyncio

from custom_logger import Logger
from database import DatabaseCreator

# Initialize the logger for the main module
logger = Logger('gwaff.main')

logger.info("Starting")

from warnings import filterwarnings

# Suppress specific warnings from the matplotlib module
filterwarnings("ignore", category=RuntimeWarning, module="matplotlib\..*", lineno=0)
filterwarnings("ignore", category=UserWarning, module="matplotlib\..*", lineno=0)

logger.info("Filtering warnings")

dbc = DatabaseCreator()
dbc.create_database()

from bot import run_the_bot

# Retrieve the bot token from environment variables
TOKEN = os.environ.get('BOT_TOKEN')

# Run the bot using the retrieved token
asyncio.run(run_the_bot(TOKEN))

logger.info("Fin!")
