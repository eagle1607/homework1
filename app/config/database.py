import configparser
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

def make_session_factory(database_uri:str):
    connect_args = {}
    engine = create_engine(database_uri, connect_args=connect_args, pool_pre_ping=True)
    session = sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
    return engine, session