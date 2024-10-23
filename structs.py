from sqlalchemy import (Column, Integer, String, DateTime,
                        ForeignKey, PrimaryKeyConstraint)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Profile(Base):
    """
    Represents a user profile in the database.

    Attributes:
        id (int): The primary key of the profile.
        name (str): The name of the profile.
        colour (str): The colour associated with the profile.
        avatar (str): The avatar URL of the profile.
    """
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    colour = Column(String)
    avatar = Column(String)

class Record(Base):
    """
    Represents a record of a profile's activity in the database.

    Attributes:
        id (int): The ID of the profile associated with this record.
        timestamp (datetime): The timestamp of the record.
        value (int): The value associated with the record.
        profile (Profile): The profile associated with this record.
    """
    __tablename__ = 'records'

    id = Column(Integer, ForeignKey('profiles.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('id', 'timestamp'),
    )

    # Relationship to Profile
    profile = relationship('Profile', back_populates='records')

Profile.records = relationship(
    'Record', order_by=Record.timestamp, back_populates='profile')

class Minecraft(Base):
    """
    Represents a Minecraft user associated with a Discord profile in the database.

    Attributes:
        discord_id (int): The Discord ID of the user.
        mc_uuid (str): The Minecraft UUID of the user.
        mc_name (str): The Minecraft name of the user.
        profile (Profile): The profile associated with this Minecraft user.
    """
    __tablename__ = 'minecraft'

    discord_id = Column(Integer, ForeignKey('profiles.id'), primary_key=True, nullable=False)
    mc_uuid = Column(String, nullable=False, unique=True)
    mc_name = Column(String)

    # Relationship to Profile
    profile = relationship('Profile', back_populates='minecraft')

Profile.minecraft = relationship('Minecraft', back_populates='profile')