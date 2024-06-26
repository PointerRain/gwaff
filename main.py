import os
import asyncio
from custom_logger import Logger
logger = Logger('gwaff.main')

from warnings import filterwarnings
filterwarnings("ignore", category=RuntimeWarning, module="matplotlib\..*", lineno=0)
filterwarnings("ignore", category=UserWarning, module="matplotlib\..*", lineno=0)

logger.info("Filtering warnings")

# from database import saveToDB, loadFromDB

# # DANGER ZONE
# # for i in db.keys():
# #     del db[i]
# # logger.info("Deleted")
# # saveToDB()
# # logger.info("Saved")

# loadFromDB()
# logger.info("Loaded")

from collector import collect
collect()
logger.info("Collecting")

TOKEN = os.environ['BOT_TOKEN']
from bot import run_the_bot
asyncio.run(run_the_bot(TOKEN))

logger.info("Fin!")
