from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker

from gwaff.database.structs import *

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.environ.get('DB_NAME', 'gwaff.db')
DB_DIR = os.path.join(BASE_DIR, DB_NAME)

print(BASE_DIR)
print(DB_NAME)
print(DB_DIR)


# logging.getLogger('sqlalchemy').disabled = True
# logging.getLogger('sqlalchemy.orm.mapper.Mapper').disabled = True
# logging.getLogger('sqlalchemy.engine.Engine').disabled = True


class BaseDatabase:
    """
    Base class for database operations using SQLAlchemy.
    """

    def __init__(self, db_dir=DB_DIR):
        """
        Initializes the database engine and session.
        """
        self.engine = create_engine(f'sqlite:///{db_dir}?charset=utf8mb4', echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def commit(self):
        """
        Commits the current transaction.
        """
        self.session.commit()

    def __del__(self):
        """
        Closes the database session.
        """
        self.session.close()


class DatabaseCreator(BaseDatabase):
    """
    Class for creating and clearing the database.
    """

    def clear_database(self):
        """
        Drops all tables in the database.
        """
        Profile.__table__.drop(self.engine, checkfirst=True)
        Record.__table__.drop(self.engine, checkfirst=True)
        MinecraftUser.__table__.drop(self.engine, checkfirst=True)
        Event.__table__.drop(self.engine, checkfirst=True)

        self.session.commit()

    def create_database(self):
        """
        Creates all tables in the database.
        """
        Base.metadata.create_all(self.engine)

        self.session.commit()


class DatabaseReader(BaseDatabase):
    """
    Class for reading data from the database.
    """

    def get_dates_in_range(self, start_date=None, end_date=None) -> list[datetime]:
        """
        Retrieves distinct timestamps within a specified date range.

        Args:
            start_date (datetime, optional): The start date of the range.
            end_date (datetime, optional): The end date of the range.

        Returns:
            list: A list of timestamps within the specified range.
        """
        query_result = self.session.query(Record.timestamp).distinct()
        if start_date and end_date:
            query_result = query_result.filter(Record.timestamp.between(start_date, end_date))
        elif start_date:
            query_result = query_result.filter(Record.timestamp >= start_date)
        return [i.timestamp for i in query_result.order_by(Record.timestamp).all()]

    def get_row(self, id: int,
                start_date: datetime = None, end_date: datetime = None) -> list[Record]:
        """
        Retrieves records for a specific ID, optionally filtering by start date.

        Args:
            id (int): The ID of the record.
            start_date (datetime, optional): The start date for filtering records.
            end_date (datetime, optional): The end date for filtering records.

        Returns:
            list: A list of records for the specified ID.
        """
        if id == 483515866319945728 and start_date < datetime(2024, 6, 2):
            if end_date is None or datetime(2024, 6, 1) < end_date:
                return []
        elif id == 457989277322838016 and start_date < datetime(2025, 1, 20):
            if end_date is None or datetime(2025, 1, 19) < end_date:
                return []
        record_query = (self.session.query(Record)
                        .filter_by(id=id)
                        .order_by(Record.timestamp))
        if start_date:
            record_query = record_query.filter(Record.timestamp >= start_date)
        if end_date:
            record_query = record_query.filter(Record.timestamp <= end_date)

        # Execute the query for records
        return record_query.all()

    def get_data_in_range(self, start_date: datetime = None, end_date: datetime = None,
                          limit: int = 15, include: set[int] = None) -> list[tuple]:
        """
        Retrieves profile data and associated records within a specified date range.

        Args:
            start_date (datetime, optional): The start date for filtering records.
            end_date (datetime, optional): The end date for filtering records.
            limit (int, optional): The maximum number of profiles to retrieve. Defaults to 15.
            include (set, optional): A list of profile IDs to include. Defaults to None.

        Returns:
            list: A list of tuples containing profile data and associated records.
        """
        profile_query = (self.session.query(Profile)
                         .join(Record, Profile.id == Record.id)
                         .group_by(Profile.id)
                         .order_by(desc(func.max(Record.value))))
        if include and hasattr(include, '__iter__'):
            profile_query = profile_query.filter(Profile.id.in_(include))
        if limit:
            profile_query = profile_query.limit(limit)

        result = []

        for profile in profile_query:
            # Query for records associated with the profile, optionally filtering by start_date
            records = self.get_row(int(profile.id), start_date, end_date)

            # Append the data to the result list
            result.append((
                (profile.id, profile.name, profile.colour, profile.avatar),
                [record.timestamp for record in records],
                [record.value for record in records]
            ))

        return result

    def get_growth_in_range(self, start_date: datetime = None, end_date: datetime = None,
                            limit: int = 15, include: set[int] = None) -> list[tuple]:
        """
        Retrieves profile data and growth within a specified date range.

        Args:
            start_date (datetime, optional): The start date for filtering records.
            end_date (datetime, optional): The end date for filtering records.
            limit (int, optional): The maximum number of profiles to retrieve. Defaults to 15.
            include (set, optional): A list of profile IDs to include. Defaults to None.
        Returns:
            list: A list of tuples containing profile data and growth values.
        """
        profile_query = (self.session.query(Profile)
                         .join(Record, Profile.id == Record.id))
        if start_date:
            profile_query = profile_query.filter(Record.timestamp >= start_date)
        if end_date:
            profile_query = profile_query.filter(Record.timestamp <= end_date)
        profile_query = (profile_query.group_by(Profile.id)
                         .order_by(desc(func.max(Record.value) - func.min(Record.value))))
        if include and hasattr(include, '__iter__'):
            profile_query = profile_query.filter(Profile.id.in_(include))
        if limit:
            profile_query = profile_query.limit(limit)

        result = []

        for profile in profile_query:
            # Query for records associated with the profile, optionally filtering by start_date
            records = self.get_row(profile.id, start_date, end_date)

            # Append the data to the result list
            result.append((
                (profile.id, profile.name, profile.colour, profile.avatar),
                [record.timestamp for record in records],
                [record.value - records[0].value for record in records]
            ))

        return result

    def get_last_timestamp(self):
        """
        Retrieves the most recent timestamp from the records.

        Returns:
            datetime: The most recent timestamp.
        """
        return self.session.query(func.max(Record.timestamp)).first()[0]

    def get_last_record(self):
        """
        Retrieves the last record for each profile.

        Returns:
            list: A list of tuples containing profile data and the maximum record value.
        """
        profile_query = (self.session.query(Profile, func.max(Record.value))
                         .join(Record, Profile.id == Record.id)
                         .group_by(Profile.id)
                         .order_by(desc(func.max(Record.value))).all())
        # return [(i, i.records[-1]) for i in profile_query]
        return profile_query

    def get_profile_data(self, id=None):
        """
        Retrieves profile data for a specific ID or all profiles if no ID is provided.

        Args:
            id (int, optional): The ID of the profile. Defaults to None.

        Returns:
            list or Profile: A list of all profiles or a specific profile.
        """
        if id is None:
            return self.session.query(Profile).all()
        return self.session.query(Profile).filter_by(id=id).first() or None


class DatabaseSaver(BaseDatabase):
    """
    Class for saving data to the database.
    """

    def update_profile(self, id, name: str = None, colour: str = None, avatar: str = None,
                       colours: list[str] = None) -> None:
        """
        Updates or creates a profile in the database.

        Args:
            id (int): The ID of the profile.
            name (str, optional): The name of the profile. Defaults to None.
            colour (str, optional): The colour of the profile. Defaults to None.
            avatar (str, optional): The avatar of the profile. Defaults to None.
            colours (list[str], optional): A list of colours of the profile. Defaults to None.
        """
        profile = self.session.query(Profile).filter_by(id=id).first()

        if profile is None:
            new_profile = Profile(id=id, name=name,
                                  colour=colour, avatar=avatar)
            self.session.add(new_profile)
            return

        profile.name = name or profile.name
        profile.colour = colour or profile.colour
        profile.avatar = avatar or profile.avatar
        profile.colours = ','.join(colours) if colours else profile.colours

    def insert_record(self, id: int, timestamp: datetime, value: int) -> None:
        """
        Inserts a new record into the database.

        Args:
            id (int): The ID of the profile.
            timestamp (datetime): The timestamp of the record.
            value (int): The xp value at the timestamp.

        Raises:
            ValueError: If id, timestamp, or value is None.
        """
        if id is None or timestamp is None or value is None:
            raise ValueError('id, timestamp, and value are required')
        new_record = Record(id=id, timestamp=timestamp, value=value)
        self.session.add(new_record)

    def load_from_csv(self, data):
        """
        Loads data from a CSV file into the database.

        Args:
            data (DataFrame): The data to load from the CSV file.
        """
        dates = data.columns
        dates = list(dates)[4:]

        for index, row in data.iterrows():
            self.update_profile(*row.iloc[0:4])
            for i in dates:
                date = datetime.fromisoformat(i)
                if row[i] is not None and not pd.isna(row[i]):
                    self.insert_record(row.iloc[0], date, int(row[i]))

        self.commit()

    def merge_database(self, other):
        """
        Merges another database into the current database.

        Args:
            other (DatabaseSaver): The other database to merge.
        """
        current = [p.id for p in self.session.query(Profile).all()]
        # print(current)
        for profile in other.session.query(Profile).all():
            if profile.id not in current:
                print(profile)
                self.session.merge(profile)

        current = [(record.id, record.timestamp) for record in self.session.query(Record).all()]
        # print(current)
        for record in other.session.query(Record).where(
                Record.timestamp > datetime(year=2025, month=1, day=10)).all():
            if (record.id, record.timestamp) not in current:
                print(record)
                self.session.merge(record)

        self.commit()


if __name__ == '__main__':
    # dbc = DatabaseCreator()
    dbr = DatabaseReader(os.path.join(BASE_DIR, 'gwaff.db'))
    # dbi = DatabaseSaver()
    #
    # # dbc.clear_database()
    # # dbc.create_database()
    #
    # # dbi.load_from_csv(pd.read_csv("gwaff.csv", index_col=0))
    #
    # print(dbr.get_profile_data())
    # print(dbr.get_profile_data()[0].__dict__)
    # print(dbr.get_profile_data(92029863090728960).__dict__)
    #
    # print(dbr.get_last_timestamp())
    # print(len(dbr.get_last_record()))
    # for p, v in dbr.get_last_record():
    #     print(p.name, v)
    # # print(dbr.get_data_in_range(limit=1))
    #
    # threshold = datetime.now() - timedelta(days=7)
    # # dates = dbr.get_dates_in_range(threshold)
    # # print(len(dates))
    # # for i in dates:
    # #     print(i)
    #
    # for i in dbr.get_data_in_range(threshold, limit=1):
    #     print(i)
    #
    # # for i in dbr.get_growth_in_range():
    # # print(i)
    # # print(i[0], i[2][-1])
    # # print(len(i[1]))
    #
    from gwaff.predictor import xp_to_lvl
    import json

    levels = {}
    for i in dbr.get_last_record():
        if i[1] <= 12017:
            continue
        # print(f'    "{i[0].id}": {xp_to_lvl(i[1])},')
        levels[str(i[0].id)] = xp_to_lvl(i[1])
    json.dump(levels, open(os.path.join(BASE_DIR, 'levels.json'), 'w'))
    print(str(levels).replace("'", '"'))

    # # MERGING DATABASES
    # dbs = DatabaseSaver(os.path.join(BASE_DIR, 'gwaff_uqcloud.db'))
    # other = DatabaseReader(os.path.join(BASE_DIR, 'gwaff_rpi.db'))
    # dbs.merge_database(other)
