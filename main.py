import os
import time

os.environ['TZ'] = 'Australia/Brisbane'
time.tzset()

print("Set the timezone")

from warnings import filterwarnings
filterwarnings("ignore", category=RuntimeWarning, module="matplotlib\..*", lineno=0)

print("Filtering warnings")

from database import saveToDB, loadFromDB
# from replit import db

# for i in db.keys():
#     del db[i]
# print('Deleted')

# saveToDB()
# print("saved")

loadFromDB()
print("Loaded")


from keep_alive import keep_alive
keep_alive()
print("Staying alive")

from collector import collect
collect()
print("Collecting")

from automate import runTheBot
TOKEN = os.environ['BOT_TOKEN']
runTheBot(TOKEN)

print("Ended!")
