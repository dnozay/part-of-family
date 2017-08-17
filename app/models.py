from sqlalchemy import Column, DateTime, Date, Integer, Sequence, String, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True, nullable=False)
    email = Column(String(64), nullable=False, index=True, unique=True)
    name = Column(String(128), nullable=False)
    password = Column(String(128))
    created_on = Column(DateTime(), server_default=func.now(), nullable=False)


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(String(64), nullable=False, primary_key=True)
    client_ip = Column(String(32), nullable=False)
    client_agent = Column(String(256))
    user_id = Column(Integer, nullable=False)
    created_on = Column(DateTime(), server_default=func.now(), nullable=False)


class DiaryEntry(Base):
    __tablename__ = 'diary_entries'

    id = Column(Integer, Sequence('diary_entry_id_seq'), primary_key=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    created_on = Column(Date(), index=True, nullable=False)
    highlights = Column(Text, nullable=False)
    moments = Column(Text, nullable=False)


sa_users = User.__table__
sa_user_sessions = UserSession.__table__
sa_diary_entries = DiaryEntry.__table__
