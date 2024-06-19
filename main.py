import os
# import time

# os.environ['TZ'] = 'Australia/Brisbane'
# time.tzset()
# print("[MAIN] Set the timezone")

from warnings import filterwarnings
filterwarnings("ignore", category=RuntimeWarning,
               module="matplotlib\..*", lineno=0)

print("[MAIN] Filtering warnings")

# from database import saveToDB, loadFromDB

# # DANGER ZONE
# # for i in db.keys():
# #     del db[i]
# # print('[MAIN] Deleted')
# # saveToDB()
# # print("[MAIN] Saved")

# loadFromDB()
# print("[MAIN] Loaded")

from collector import collect
collect()
print("[MAIN] Collecting")

TOKEN = os.environ['BOT_TOKEN']
from bot import run_the_bot
run_the_bot(TOKEN)

print("[MAIN] Fin!")
