import os
import asyncio
import logging
from warnings import filterwarnings

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)8s [%(asctime)s] %(filename)13s | %(message)s',
                    datefmt='%H:%M:%S')

filterwarnings("ignore", category=RuntimeWarning, module="matplotlib\..*", lineno=0)
filterwarnings("ignore", category=UserWarning, module="matplotlib\..*", lineno=0)

logging.info("Filtering warnings")

# from database import saveToDB, loadFromDB

# # DANGER ZONE
# # for i in db.keys():
# #     del db[i]
# # logging.info("Deleted")
# # saveToDB()
# # logging.info("Saved")

# loadFromDB()
# logging.info("Loaded")

from collector import collect
collect()

TOKEN = os.environ['BOT_TOKEN']
from bot import run_the_bot
asyncio.run(run_the_bot(TOKEN))

logging.info("Fin!")
