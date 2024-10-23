from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker

from structs import *

MAX_RETRIES = 5

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'gwaff.db')

class BaseDatabase:
    """
    Base class for database operations using SQLAlchemy.
    """
    def __init__(self):
        """
        Initializes the database engine and session.
        """
        self.engine = create_engine(f'sqlite:///{DB_DIR}', echo=False)
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
        Minecraft.__table__.drop(self.engine, checkfirst=True)

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
    def get_dates_in_range(self, start_date=None, end_date=None):
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
            return [i.timestamp for i in query_result.filter(Record.timestamp
                                                     .between(start_date, end_date)).all()]
        elif start_date:
            return [i.timestamp for i in query_result.filter(Record.timestamp >= start_date).all()]
        return [i.timestamp for i in query_result.all()]

    def get_row(self, id, start_date=None):
        """
        Retrieves records for a specific ID, optionally filtering by start date.

        Args:
            id (int): The ID of the record.
            start_date (datetime, optional): The start date for filtering records.

        Returns:
            list: A list of records for the specified ID.
        """
        if id in [483515866319945728]:
            return []
        record_query = (self.session.query(Record)
                                    .filter_by(id=id)
                                    .order_by(Record.timestamp))
        if start_date:
            record_query = record_query.filter(Record.timestamp >= start_date)

        # Execute the query for records
        return record_query.all()

    def get_data_in_range(self, start_date=None, limit=15):
        """
        Retrieves profile data and associated records within a specified date range.

        Args:
            start_date (datetime, optional): The start date for filtering records.
            limit (int, optional): The maximum number of profiles to retrieve. Defaults to 15.

        Returns:
            list: A list of tuples containing profile data and associated records.
        """
        profile_query = (self.session.query(Profile)
                                     .join(Record, Profile.id == Record.id)
                                     .group_by(Profile.id)
                                     .order_by(desc(func.max(Record.value)))
                                     .limit(limit))

        result = []

        for profile in profile_query:
            # Query for records associated with the profile, optionally filtering by start_date
            records = self.get_row(profile.id, start_date)

            # Append the data to the result list
            result.append((
                (profile.id, profile.name, profile.colour, profile.avatar),
                [record.timestamp for record in records],
                [record.value for record in records]
            ))

        return result

    def get_growth_in_range(self, start_date=None, limit=15):
        """
        Retrieves profile data and growth within a specified date range.

        Args:
            start_date (datetime, optional): The start date for filtering records.
            limit (int, optional): The maximum number of profiles to retrieve. Defaults to 15.

        Returns:
            list: A list of tuples containing profile data and growth values.
        """
        if start_date:
            profile_query = (self.session.query(Profile)
                                         .join(Record, Profile.id == Record.id)
                                         .filter(Record.timestamp >= start_date))
        else:
            profile_query = (self.session.query(Profile)
                                         .join(Record, Profile.id == Record.id))
        profile_query = (profile_query.group_by(Profile.id)
                                      .order_by(desc(func.max(Record.value) - func.min(Record.value)))
                                      .having(Profile.id != 1013000925385871451)
                                      .having(Profile.id != 483515866319945728)
                                      .limit(limit))

        result = []

        for profile in profile_query:
            # Query for records associated with the profile, optionally filtering by start_date
            records = self.get_row(profile.id, start_date)

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
    def update_profile(self, id, name=None, colour=None, avatar=None):
        """
        Updates or creates a profile in the database.

        Args:
            id (int): The ID of the profile.
            name (str, optional): The name of the profile. Defaults to None.
            colour (str, optional): The colour of the profile. Defaults to None.
            avatar (str, optional): The avatar of the profile. Defaults to None.
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

    def insert_record(self, id, timestamp, value):
        """
        Inserts a new record into the database.

        Args:
            id (int): The ID of the profile.
            timestamp (datetime): The timestamp of the record.
            value (int): The value of the record.

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


if __name__ == '__main__':
    # dbc = DatabaseCreator()
    dbr = DatabaseReader()
    # dbi = DatabaseSaver()

    # dbc.clear_database()
    # dbc.create_database()

    # dbi.load_from_csv(pd.read_csv("gwaff.csv", index_col=0))

    print(dbr.get_profile_data())
    print(dbr.get_profile_data()[0].__dict__)
    print(dbr.get_profile_data(92029863090728960).__dict__)

    print(dbr.get_last_timestamp())
    print(len(dbr.get_last_record()))
    for p, v in dbr.get_last_record():
        print(p.name, v)
    # print(dbr.get_data_in_range(limit=1))

    threshold = datetime.now() - timedelta(days=7)
    # dates = dbr.get_dates_in_range(threshold)
    # print(len(dates))
    # for i in dates:
    #     print(i)

    for i in dbr.get_data_in_range(threshold, limit=1):
        print(i)

    # for i in dbr.get_growth_in_range():
        # print(i)
        # print(i[0], i[2][-1])
        # print(len(i[1]))

    # for i in dbr.get_profile_data():
    #     print(i.__dict__)