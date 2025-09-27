import os
import time
from datetime import datetime
from threading import Thread
from typing import Iterable

from gwaff.database.db_base import DatabaseReader, DatabaseSaver
from gwaff.custom_logger import Logger
from gwaff.utils import request_api

logger = Logger('gwaff.collect')

MAX_RETRIES: int = 5  # How many times to attempt to collect and save data

WAIT_SUCCESS: int = 60  # How many minutes to wait after a success. Deprecated.
WAIT_FAIL: int = 30  # How many minutes to wait after a failure. Deprecated.

MIN_SEPARATION: int = int(os.environ.get("MIN_SEPARATION", 30))
COLLECTION_SMALL: int = int(os.environ.get("COLLECTION_SMALL", 2))
COLLECTION_LARGE: int = int(os.environ.get("COLLECTION_LARGE", 6))
COLLECTION_LARGEST: int = int(os.environ.get("COLLECTION_LARGEST", 10))

SERVER_ID = os.environ.get("TRACKING_SERVER")
API_URL = os.environ.get("API_URL")


class TooSoonException(Exception):
    """
    Exception raised when the data collection is attempted too soon after the last collection.
    """
    pass


class ManyFailuresException(Exception):
    """
    Exception raised when there are many failures during data collection.
    """
    pass


def record_data(pages: Iterable[int] = range(1, COLLECTION_LARGE),
                min_time: int = MIN_SEPARATION, add_records=True) -> None:
    """
    Record the current XP data and ensure records are separated by at least min_time minutes.

    Args:
        pages (Iterable[int]): The pages to collect data from. Defaults to range(1, COLLECTION_LARGE).
        min_time (int): Minimum time in minutes between data collections. Defaults to MIN_SEPARATION.
        add_records (bool): Whether to add records to the database. Defaults to True.

    Throws:
        TooSoonException: If the collection time was too close to previous time
        ManyFailuresException: If there were many errors when updating records.
        Exception (db.commit): If there was an error while commiting the data to the db.
    """
    logger.info("Starting data collection")

    # Check if enough time has passed since the last collection
    lasttime = DatabaseReader().get_last_timestamp()
    now = datetime.now()
    if (now - lasttime).total_seconds() < min_time * 60:
        logger.info(f"Too soon - {int((now - lasttime).total_seconds() / 60)}/{min_time} minutes required")
        raise TooSoonException(f"Too soon - {int((now - lasttime).total_seconds() / 60)}/{min_time} minutes required")

    dbi = DatabaseSaver()
    success, failure = 0, 0

    # Collect data from pages
    for page in pages:
        data = request_api(API_URL, page=page)
        if not data:
            logger.error("Skipping page after max retries")
            failure += 100
            continue

        for member in data.get('leaderboard', []):
            if 'missing' in member or member.get('color', '#000000') == '#000000':
                continue

            member_id, xp = member.get('id'), member.get('xp')
            name = member.get('nickname') or member.get('displayName') or member.get('username')
            if not all([member_id, xp]):
                logger.warning(f"Skipping record with missing data")
                failure += 1
                continue

            # Retry updating profile and inserting record
            for attempt in range(MAX_RETRIES):
                try:
                    if add_records:
                        dbi.insert_record(int(member_id), now, int(xp))
                    dbi.update_profile(int(member_id), name, member.get('color'), member.get('avatar'),
                                       member.get('colors', None))
                    success += 1
                    break
                except Exception as e:
                    logger.warning(f"Failed to add record (attempt {attempt + 1}): {str(e)}")
                    failure += 1
                    break
            else:
                logger.error(f"Skipping record after max retries")

    # Commit changes with retries
    for attempt in range(MAX_RETRIES):
        try:
            dbi.commit()
            break
        except Exception as e:
            logger.warning(f"Failed to commit database (attempt {attempt + 1}): {str(e)}")
            continue
    else:
        raise Exception("Failed to commit database after retries")

    if success > failure:
        logger.info("Successfully saved the latest data!")
    else:
        logger.error("Considerable record save failures!")
        raise ManyFailuresException("Considerable record save failures!")


def run() -> None:
    """
    Periodically collects data. Should not be used if the bot is running.
    """
    while True:
        try:
            record_data(pages=range(1, COLLECTION_LARGE + 1))
        except Exception:
            success = False
        else:
            success = True
        wait = WAIT_SUCCESS if success else WAIT_FAIL

        for i in range(wait // 10):
            logger.debug(f"Slept {i * 10}/{wait} minutes")
            time.sleep(10 * 60)

        try:
            record_data(pages=range(1, COLLECTION_SMALL + 1))
        except Exception:
            success = False
        else:
            success = True
        wait = WAIT_SUCCESS if success else WAIT_FAIL

        for i in range(wait // 10):
            logger.debug(f"Slept {i * 10}/{wait} minutes")
            time.sleep(10 * 60)


def collect() -> None:
    """
    Creates a thread to periodically collect data. Should not be used if bot is running.
    """
    t = Thread(target=run)
    t.start()


if __name__ == '__main__':
    collect()
    logger.info("Collection started")
