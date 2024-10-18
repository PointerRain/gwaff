from sqlalchemy import (create_engine, Column, Integer, String, DateTime,
                        ForeignKey, PrimaryKeyConstraint, func, desc)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True)
    nickname = Column(String, nullable=False)
    colour = Column(String)
    avatar = Column(String)


class Record(Base):
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
    __tablename__ = 'minecraft'

    discord_id = Column(Integer, ForeignKey('profiles.id'), primary_key=True, nullable=False)
    mc_uuid = Column(String, nullable=False, unique=True)
    mc_name = Column(String)

    # Relationship to Profile
    profile = relationship('Profile', back_populates='minecraft')


Profile.minecraft = relationship('Minecraft', back_populates='profile')
