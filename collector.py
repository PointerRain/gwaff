from urllib.parse import urlencode
import requests
import json
import time
import pandas as pd
from datetime import datetime
from threading import Thread

from database import DatabaseReader, DatabaseSaver
from custom_logger import Logger

logger = Logger('gwaff.collect')

from database import saveToDB

MAX_RETRIES: int = 5        # How many times to attempt to collect and save data
WAIT_SUCCESS: int = 120     # How many minutes to wait after a success
WAIT_FAIL: int = 30         # How many minutes to wait after a failure
MIN_SEPARATION: int = 60    # Do not store new data if the last collection was
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
    while count < MAX_RETRIES:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.json()
        except Exception as e:
            logger.warning(f"Attempt {count+1} failed: {str(e)}")
            if count < MAX_RETRIES:
                count += 1
                time.sleep(1 << count)
            else:
                logger.error("Max retries reached, skipping collection")
                return None


def url_constructor(base: str, **kwargs: dict) -> str:
    '''
    Constructs a url from a base url and several key-values.

    Returns: str of the final url.
    '''
    query = urlencode(kwargs)
    return f"{base}?{query}"


def record_data(pages: list = range(1, COLLECTION_LARGE),
                min_time: int = MIN_SEPARATION) -> bool:
    '''
    Record the current XP data and ensure records are separated by at least min_time minutes.

    Returns: bool representing if data was successfully gathered.
    '''
    logger.info("Starting data collection")

    dbr = DatabaseReader()
    lasttime = dbr.get_last_timestamp()
    now = datetime.now()

    difference = now - lasttime
    if difference.total_seconds() < min_time * 60:
        logger.info(f"Too soon - {int(difference.total_seconds() / 60)} minutes/{min_time} minutes required")
        return False

    dbi = DatabaseSaver()
    success, failure = (0, 0)

    for page in pages:
        url = url_constructor(API_URL, page=page)
        data = request_api(url)
        if not data:
            return False

        leaderboard = data.get('leaderboard', [])

        for member in leaderboard:
            if 'missing' not in member and member['color'] != '#000000':
                count = 0
                while count < MAX_RETRIES:
                    try:
                        # Extract member data
                        member_id = int(member['id'])
                        xp = member['xp']
                        name = member.get('nickname') or member.get(
                            'displayName') or member.get('username')
                        colour = member['color']
                        avatar = member['avatar']

                        # Update profile and record
                        dbi.update_profile(member_id, name, colour, avatar)
                        dbi.insert_record(member_id, now, xp)

                        success += 1
                        break  # Exit retry loop on success
                    except Exception as e:
                        logger.warning(f"Failed to save record (attempt {count+1}): {str(e)}")
                        if count < MAX_RETRIES:
                            count += 1
                        else:
                            logger.error("Skipping record after max retries")
                            failure += 1
                            break

        logger.debug(f"Page {page} collected")

    dbi.commit()

    if success > failure:
        logger.info("Successfully saved the latest data!")
        return True
    else:
        logger.error("Considerable record save failures!")
        return False


def run() -> None:
    '''
    Periodically collects data.
    '''
    while True:
        success = record_data(pages=range(1, COLLECTION_LARGE))
        wait = WAIT_SUCCESS if success else WAIT_FAIL

        for i in range(wait // 10):
            logger.debug(f"Slept {i * 10}/{wait} minutes")
            time.sleep(10 * 60)

        success = record_data(pages=range(1, COLLECTION_SMALL))
        wait = WAIT_SUCCESS if success else WAIT_FAIL

        for i in range(wait // 10):
            logger.debug(f"Slept {i * 10}/{wait} minutes")
            time.sleep(10 * 60)


def collect() -> None:
    '''
    Creates a thread to periodically collect data.
    '''
    t = Thread(target=run)
    t.start()


if __name__ == '__main__':
    collect()
    logger.info("Collection started")
