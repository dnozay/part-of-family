from sqlalchemy import Column, DateTime, Integer, Sequence, String, func
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


sa_users = User.__table__
sa_user_sessions = UserSession.__table__
