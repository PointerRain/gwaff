import os
import time

os.environ['TZ'] = 'Australia/Brisbane'
time.tzset()

print("[MAIN] Set the timezone")

from warnings import filterwarnings
filterwarnings("ignore", category=RuntimeWarning,
               module="matplotlib\..*", lineno=0)

print("[MAIN] Filtering warnings")

from database import saveToDB, loadFromDB

# for i in db.keys():
#     del db[i]
# print('[MAIN] Deleted')

# saveToDB()
# print("[MAIN] Saved")

loadFromDB()
print("[MAIN] Loaded")


from keep_alive import keep_alive
keep_alive()
print("[MAIN] Staying alive")

from collector import collect
collect()
print("[MAIN] Collecting")

from bot import runTheBot
TOKEN = os.environ['BOT_TOKEN']
runTheBot(TOKEN)

print("[MAIN] Fin!")
