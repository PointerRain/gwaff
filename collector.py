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
                min_time: int = MIN_SEPARATION) -> None:
    """
    Record the current XP data and ensure records are separated by at least min_time minutes.

    Args:
        pages (Iterable[int]): The pages to collect data from. Defaults to range(1, COLLECTION_LARGE).
        min_time (int): Minimum time in minutes between data collections. Defaults to MIN_SEPARATION.

    Throws:
        TooSoonException: If the collection time was too close to previous time
        ManyFailuresException: If there were many errors when updating records.
        Exception (db.commit): If there was an error while commiting the data to the db.
    """
    logger.info("Starting data collection")

    dbr = DatabaseReader()
    lasttime = dbr.get_last_timestamp()
    now = datetime.now()

    difference = now - lasttime
    if difference.total_seconds() < min_time * 60:
        logger.info(
            f"Too soon - {int(difference.total_seconds() / 60)}/{min_time} minutes required")
        raise TooSoonException(
            f"Too soon - {int(difference.total_seconds() / 60)}/{min_time} minutes required")

    dbi = DatabaseSaver()
    success, failure = (0, 0)

    for page in pages:
        data = request_api(API_URL, page=page)
        if not data:
            logger.error("Skipping page after max retries")
            failure += 100
            continue

        leaderboard = data.get('leaderboard', [])

        for member in leaderboard:
            if 'missing' in member or member.get('color', '#000000') == '#000000':
                continue

            # Extract member data
            member_id = member.get('id')
            xp = member.get('xp')
            name = (member.get('nickname')
                    or member.get('displayName')
                    or member.get('username'))
            colour = member.get('color')
            avatar = member.get('avatar')
            if any(x is None for x in (member_id, xp)):
                logger.warning(f"Skipping record with missing data")
                failure += 1
                continue

            count = 0
            while count < MAX_RETRIES:
                try:
                    # Update profile and record
                    dbi.update_profile(int(member_id), name, colour, avatar)
                    dbi.insert_record(int(member_id), now, int(xp))

                    success += 1
                    break  # Exit retry loop on success
                except Exception as e:
                    logger.warning(f"Failed to add record (attempt {count + 1}): {str(e)}")
                    if count < MAX_RETRIES:
                        count += 1
                    else:
                        logger.error("Skipping record after max retries")
                        failure += 1
                        break

        logger.debug(f"Page {page} collected")

    count = 0
    while count < MAX_RETRIES:
        try:
            dbi.commit()
        except Exception as e:
            logger.warning(f"Failed to commit database (attempt {count + 1}): {str(e)}")
            if count < MAX_RETRIES:
                count += 1
            else:
                logger.error("Skipping commit after max retries")
                raise e
        else:
            break

    if success > failure:
        logger.info("Successfully saved the latest data!")
        return
    else:
        logger.error("Considerable record save failures!")
        raise ManyFailuresException(f"Considerable record save failures!")


def update_profiles(pages: Iterable[int] = range(1, COLLECTION_LARGEST)) -> None:
    logger.info("Starting profile collection")

    dbi = DatabaseSaver()
    success, failure = (0, 0)

    for page in pages:
        data = request_api(API_URL, page=page)
        if not data:
            logger.error("Skipping page after max retries")
            continue

        leaderboard = data.get('leaderboard', [])

        for member in leaderboard:
            if 'missing' not in member and member.get('color', '#000000') != '#000000':
                count = 0
                while count < MAX_RETRIES:
                    try:
                        # Extract member data
                        member_id = int(member.get('id'))
                        name = (member.get('nickname')
                                or member.get('displayName')
                                or member.get('username'))
                        colour = member.get('color')
                        avatar = member.get('avatar')

                        if member_id is None:
                            logger.warning(f"Skipping profile with missing data")
                            failure += 1
                            break

                        # Update profile
                        dbi.update_profile(member_id, name, colour, avatar)

                        success += 1
                        break  # Exit retry loop on success
                    except Exception as e:
                        logger.warning(f"Failed to save record (attempt {count + 1}): {str(e)}")
                        if count < MAX_RETRIES:
                            count += 1
                        else:
                            logger.error("Skipping record after max retries")
                            failure += 1
                            break

        logger.debug(f"Page {page} updated")

    dbi.commit()


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
