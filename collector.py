import time
from datetime import datetime
from threading import Thread
from typing import Iterable

from database import DatabaseReader, DatabaseSaver
from custom_logger import Logger
from utils import request_api

logger = Logger('gwaff.collect')

MAX_RETRIES: int = 5        # How many times to attempt to collect and save data
WAIT_SUCCESS: int = 60      # How many minutes to wait after a success
WAIT_FAIL: int = 30         # How many minutes to wait after a failure
MIN_SEPARATION: int = 30    # Do not store new data if the last collection was
                            #  less than this many minutes ago
COLLECTION_SMALL: int = 3   # Collect data from up to this page every
                            #  collection event
COLLECTION_LARGE: int = 8   # Collect data from up to this page every second
                            #  collection event
SERVER_ID = "377946908783673344"
API_URL = f"https://gdcolon.com/polaris/api/leaderboard/{SERVER_ID}"

def record_data(pages: Iterable[int] = range(1, COLLECTION_LARGE),
                min_time: int = MIN_SEPARATION) -> bool:
    """
    Record the current XP data and ensure records are separated by at least min_time minutes.

    Args:
        pages (Iterable[int]): The pages to collect data from. Defaults to range(1, COLLECTION_LARGE).
        min_time (int): Minimum time in minutes between data collections. Defaults to MIN_SEPARATION.

    Returns:
        bool: True if data was successfully gathered, False otherwise.
    """
    logger.info("Starting data collection")

    dbr = DatabaseReader()
    lasttime = dbr.get_last_timestamp()
    now = datetime.now()

    difference = now - lasttime
    if difference.total_seconds() < min_time * 60:
        logger.info(f"Too soon - {int(difference.total_seconds() / 60)}/{min_time} minutes required")
        return False

    dbi = DatabaseSaver()
    success, failure = (0, 0)

    for page in pages:
        data = request_api(API_URL, page=page)
        if not data:
            logger.error("Skipping page after max retries")
            continue

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
    """
    Periodically collects data.
    """
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
    """
    Creates a thread to periodically collect data.
    """
    t = Thread(target=run)
    t.start()

if __name__ == '__main__':
    collect()
    logger.info("Collection started")