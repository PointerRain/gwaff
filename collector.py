from urllib.request import Request, urlopen
import requests
import json
import time
import pandas as pd
from datetime import datetime
from threading import Thread

from custom_logger import Logger
logger = Logger('gwaff.collect')

from database import saveToDB

MAX_RETRIES: int = 5        # How many times to attempt to collect and save data
WAIT_SUCCESS: int = 120     # How many minutes to wait after a success
WAIT_FAIL: int = 30         # How many minutes to wait after a failure
MIN_SEPERATION: int = 60    # Do not store new data if the last collection was
                            #  less than this many minutes ago
COLLECTION_SMALL: int = 3   # Collect data from up to this page every 
                            #  collection event
COLLECTION_LARGE: int = 8   # Collect data from up to this page every second 
                            #  collection event
SERVER_ID = "377946908783673344"
API_URL = f"https://gdcolon.com/polaris/api/leaderboard/{SERVER_ID}"


def request_api(url: str) -> dict:
    '''
    Requests data from the given api.

    Returns: dict of the requested data.
    '''
    count = 0
    while True:
        try:
            request = Request(url)
            request.encoding = 'utf-8'
            data = urlopen(request).read()
            return json.loads(data)
        except Exception as e:
            logger.warning(f"Could not retrieve {str(count)}")
            print(e)
            if count < MAX_RETRIES:
                count += 1
                time.sleep(2**count)
            else:
                logger.error("Skipping")
                return None


def url_constructor(base: str, **kwargs: dict) -> str:
    '''
    Constructs a url from a base url and several key-values.

    Returns: str of the final url.
    '''
    if kwargs:
        keys = list(kwargs.keys())
        url = f"{base}?{keys[0]}={kwargs[keys[0]]}"
        for kw in keys[1:]:
            url += f"&{kw}={kwargs[kw]}"
    return url


def record_data(pages: list = range(1, COLLECTION_LARGE),
                min_time: int = WAIT_FAIL) -> bool:
    '''
    Record the current xp data to gwaff.csv.
    Ensures records are seperated by at least min_time.

    Returns: bool representing if data was successfully gathered.
    '''

    logger.info("Collecting!")

    ids = []
    names = []
    colours = []
    avatars = []

    xps = {}

    # Open the last copy of the data.
    last = pd.read_csv("gwaff.csv", index_col=0)

    for page in pages:
        url = url_constructor(API_URL, page=page)

        data = request_api(url)
        if not data:
            return False
        leaderboard = data['leaderboard']

        for member in leaderboard:
            if not ('missing' in member or member['color'] == '#000000'):
                # Save xp and ids
                id = int(member['id'])
                ids.append(id)
                xp = member['xp']
                xps[id] = xp
                # Update names, colours, and avatars
                name = member['nickname'] \
                    or member['displayName'] \
                    or member['username']
                last.loc[last['ID'] == id, 'Name'] = name
                colour = member['color']
                last.loc[last['ID'] == id, 'Colour'] = colour
                avatar = member['avatar']
                last.loc[last['ID'] == id, 'Avatar'] = avatar
                # Also append to lists
                names.append(name)
                colours.append(colour)
                avatars.append(avatar)

        logger.debug(f"- Page {page} collected")

    # Below saves the data
    struct = {'ID': ids, 'Name': names, 'Colour': colours, 'Avatar': avatars}

    lasttime = last.columns[-1]
    lasttime = datetime.fromisoformat(lasttime)
    logger.info(f"Last: {str(lasttime)}")
    now = datetime.now()
    logger.info(f" Now: {str(now)}")
    difference = now - lasttime
    logger.info(f"Diff: {str(difference)}")

    # Checks before saving. Could be improved
    if difference.total_seconds() > min_time * 60 * 60:
        other = pd.DataFrame(struct)
        df = pd.concat([last, other])
        df = df.drop_duplicates('ID', keep='first')

        newxp = []
        for index, row in df.iterrows():
            if row['ID'] in xps:
                newxp.append(xps[row['ID']])
            else:
                newxp.append(None)
        df[now] = newxp

        count = 0
        while True:
            try:
                df.to_csv('gwaff.csv', encoding='utf-8')
                saveToDB()
            except Exception as e:
                logger.warning(f"Could not save {str(count)}")
                print(e)
                if count < MAX_RETRIES:
                    count += 1
                else:
                    logger.error("Skipping")
                    return False
            else:
                logger.info("Saved latest data!")
                break

        return True

    else:
        logger.info(f"Too soon - {int(difference.total_seconds() / 60)}/{min_time * 60}")
        return False


def run() -> None:
    '''
    Periodically collects data.
    '''
    while True:
        success = record_data(min_time=1, pages=range(1, COLLECTION_LARGE))
        wait = WAIT_SUCCESS if success else WAIT_FAIL

        for i in range(wait//10):
            logger.debug(f"Slept {i * 10}/{wait}")
            time.sleep(10 * 60)

        success = record_data(min_time=1, pages=range(1, COLLECTION_SMALL))
        wait = WAIT_SUCCESS if success else WAIT_FAIL

        for i in range(wait//10):
            logger.debug(f"Slept {i * 10}/{wait}")
            time.sleep(10 * 60)


def collect() -> None:
    '''
    Creates a thread to periodically collect data.
    '''
    t = Thread(target=run)
    t.start()


if __name__ == '__main__':
    collect()

    logger.info("Collection Started")
