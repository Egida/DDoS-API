import databases
import sqlalchemy
import traceback
from sqlalchemy import Column, String, Integer, Boolean, create_engine, select
from sqlalchemy.ext.declarative import declarative_base

database, metadata = databases.Database("sqlite:///data/keys.db"), sqlalchemy.MetaData()

Base = declarative_base()

class Key(Base):
    __tablename__ = "key"
    user, key, time, concurrents, admin, premium = Column(String, primary_key=True), Column(String), Column(Integer), Column(Integer), Column(Boolean), Column(Boolean)

Base.metadata.create_all(create_engine("sqlite:///data/keys.db"))

async def fetch_key(query, key_type, value):
    try:
        query = select([Key]).where(getattr(Key, key_type) == value)
        return await database.fetch_one(query)
    except:
        print(traceback.format_exc())
        return False

async def key_check(key_type, value):
    return await fetch_key(select([Key]), key_type, value)

async def admin_check(key_type, value):
    try: return dict((await fetch_key(select([Key]), key_type, value))).get("admin", False)
    except: 
        print(traceback.format_exc())
        return False

async def premium_check(key_type, value):
    try: return dict((await fetch_key(select([Key]), key_type, value))).get("premium", False)
    except: 
        print(traceback.format_exc()) 
        return False