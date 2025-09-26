import datetime
import os

from gwaff.database.db_base import BaseDatabase
from gwaff.database.structs import Profile, Record

XP_SAFE_THRESHOLD = int(os.environ.get("XP_SAFE_THRESHOLD", 200))


class DatabaseReducer(BaseDatabase):
    """
    Class used to reduce the number of date entries in the database.
    """

    def reduce(self):
        """
        Reduces the number of records in the database.

        For each user, iterates over all their records and removes any row
        with a timestamp that is less than two hours from the previous and
        next timestamp.
        """
        profile_query = self.session.query(Profile).all()

        delete_count: int = 0

        now = datetime.datetime.now()

        for user in profile_query:
            records = (self.session.query(Record)
                       .filter_by(id=user.id)
                       .order_by(Record.timestamp).all())

            if len(records) <= 3:
                continue

            to_delete = set()

            i = 1
            prev_record = records[0]
            while i < len(records) - 1:
                curr_record = records[i]
                next_record = records[i + 1]

                # if any(record in to_delete for record in {prev_record, curr_record, next_record}):
                #     print("Skipping due to previous deletion")
                #     continue

                timediff = next_record.timestamp - prev_record.timestamp
                valdiff = next_record.value - prev_record.value
                age = now - curr_record.timestamp

                if valdiff < 0:
                    print(
                        f"user: {user.name}, prev: {prev_record.value}, curr: {curr_record.value}, next: {next_record.value}")

                if (timediff < datetime.timedelta(hours=3)
                        and valdiff < XP_SAFE_THRESHOLD
                        and age > datetime.timedelta(days=30)):
                    to_delete.add(curr_record)
                elif (timediff < datetime.timedelta(hours=6)
                      and valdiff < XP_SAFE_THRESHOLD
                      and age > datetime.timedelta(days=365)):
                    to_delete.add(curr_record)
                elif (valdiff == 0
                      and timediff < datetime.timedelta(hours=12)
                      and age > datetime.timedelta(days=7)):
                    to_delete.add(curr_record)
                else:
                    prev_record = curr_record
                i += 1

            delete_count += len(to_delete)
            for record in to_delete:
                self.session.delete(record)
        return delete_count


if __name__ == '__main__':
    dr = DatabaseReducer()

    confirm = input('Do you want to run the reducer? (Y or n)\n')
    # confirm = 'Y'
    if confirm == 'Y':
        count = dr.reduce()
        if count > 0:
            print(f'Deleting {count} records')
            confirm = input('Are you really sure? (Y or n)\n')
            if confirm == 'Y':
                dr.commit()
            else:
                print('Aborted')
        else:
            print('0 records deleted')
    else:
        print('Aborted')
