from sqlalchemy import (create_engine, Column, Integer, String, DateTime,
                        ForeignKey, PrimaryKeyConstraint, func, desc)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timedelta
import time
import pandas as pd

from structs import *


class BaseDatabase():
    def __init__(self):
        self.engine = create_engine('sqlite:///gwaff.db')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def commit(self):
        self.session.commit()


class DatabaseCreator(BaseDatabase):
    def clear_database(self):
        Profile.__table__.drop(self.engine, checkfirst=True)
        Record.__table__.drop(self.engine, checkfirst=True)
        Minecraft.__table__.drop(self.engine, checkfirst=True)

        self.session.commit()

    def create_database(self):

        Base.metadata.create_all(self.engine)

        self.session.commit()


class DatabaseReader(BaseDatabase):
    def get_dates_in_range(self, start_date=None, end_date=None):
        query_result = self.session.query(Record)
        if start_date and end_date:
            return [i.timestamp for i in query_result.filter(Record.timestamp.between(start_date, end_date)).all()]
        elif start_date:
            return [i.timestamp for i in query_result.filter(Record.timestamp >= start_date).all()]
        return [i.timestamp for i in query_result.all()]

    def get_row(self, id, start_date=None):
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
        '''
        Returns a tuple of three tuples.
        The first contains profile data, the second contains timestamps, and the third contains the corresponding values.
        SELECT id, nickname, colour, avatar
        '''
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
                (profile.id, profile.nickname, profile.colour, profile.avatar),
                [record.timestamp for record in records],
                [record.value for record in records]
            ))

        return result

    def get_growth_in_range(self, start_date=None, limit=15):
        '''
        Returns a tuple of three tuples.
        The first contains profile data, the second contains timestamps, and the third contains the corresponding values.
        SELECT id, nickname, colour, avatar, minimum xp in range
        '''
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
                (profile.id, profile.nickname, profile.colour, profile.avatar),
                [record.timestamp for record in records],
                [record.value - records[0].value for record in records]
            ))

        return result

    def get_last_date(self):
        return self.session.query(func.max(Record.timestamp)).first()

    def get_last_record(self):
        return self.session.query(Record).last()

    def get_profile_data(self):
        return self.session.query(Profile).all()


class DatabaseSaver(BaseDatabase):
    def update_profile(self, id, nickname=None, colour=None, avatar=None):
        profile = self.session.query(Profile).filter_by(id=id).first()

        if profile is None:
            new_profile = Profile(id=id, nickname=nickname,
                                  colour=colour, avatar=avatar)
            self.session.add(new_profile)
            return

        profile.nickname = nickname or profile.nickname
        profile.colour = colour or profile.colour
        profile.avatar = avatar or profile.avatar

    def insert_record(self, id, timestamp, value):
        if id is None or timestamp is None or value is None:
            raise ValueError('id, timestamp, and value are required')
        new_record = Record(id=id, timestamp=timestamp, value=value)
        self.session.add(new_record)

    def load_from_csv(self, data):
        dates = data.columns
        dates = list(dates)[4:]

        for index, row in data.iterrows():
            self.update_profile(*row.iloc[0:4])
            for i in dates:
                date = datetime.fromisoformat(i)
                if row[i] is not None and not pd.isna(row[i]):
                    self.insert_record(row.iloc[0], date, int(row[i]))

        self.commit()


class DatabaseMinecraft(BaseDatabase):
    def load_from_csv(self, data):
        for index, row in data.iterrows():
            self.add_user(row.iloc[0], row.iloc[1], row.iloc[3])

        self.commit()

    def add_user(self, discord_id, mc_uuid, mc_name):
        if pd.isna(mc_uuid):
            return

        user = self.session.query(Minecraft).filter_by(
            discord_id=discord_id).first()

        if user is not None:
            print('Updating')
            user.mc_uuid = mc_uuid or user.mc_uuid
            user.mc_name = mc_name or user.mc_name
            return

        print('Making new')
        new_user = Minecraft(discord_id=discord_id, mc_uuid=mc_uuid,
                             mc_name=mc_name)
        self.session.add(new_user)

    def get_users(self):
        return self.session.query(Minecraft).join(Profile, Minecraft.discord_id == Profile.id).all()



dbc = DatabaseCreator()
dbr = DatabaseReader()
dbi = DatabaseSaver()
dbm = DatabaseMinecraft()

# dbm.load_from_csv(pd.read_csv("users_withnames.csv"))

for i in dbm.get_users():
    print(i.discord_id, i.profile.nickname, i.mc_name)

# dbc.clear_database()
# dbc.create_database()

# dbi.load_from_csv(pd.read_csv("gwaff.csv", index_col=0))

# print(dbr.get_profile_data())
# print(dbr.get_profile_data()[0].__dict__)
# print(dbr.get_dates_in_range())
# print(dbr.get_last_date())
# print(dbr.get_data_in_range(limit=1))

# threshold = datetime.now() - timedelta(days=7)

# for i in dbr.get_growth_in_range(limit=4):
#     print(i)

# print()
# dbi.update_profile(103,'Stormi','blue')
# dbi.commit()

# for i in dbr.get_growth_in_range():
    # print(i)
    # print(i[0], i[2][-1])
    # print(len(i[1]))

# for i in dbr.get_profile_data():
#     print(i.__dict__)
