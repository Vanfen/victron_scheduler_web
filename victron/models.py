from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.types import LargeBinary

from database import base_class


Base = base_class.Base
class VictronEnergy(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(LargeBinary, index=True)
    portal_id = Column(String)
    price_to_compare = Column(Float)

    user_id = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"))

class VictronAvailableSchedules(Base):
    id = Column(Integer, primary_key=True, index=True)
    first = Column(Boolean)
    second = Column(Boolean)
    third = Column(Boolean)
    fourth = Column(Boolean)
    fifth = Column(Boolean)

    user_id = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"))

class VictronSchedulesToFill(Base):
    id = Column(Integer, primary_key=True, index=True)
    to_fill = Column(String)

    user_id = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"))

class VictronScheduleHistory(Base):
    id = Column(Integer, primary_key=True, index=True)
    schedule_time = Column(String)
    duration = Column(Integer)
    schedult_id = Column(String)
    update_time = Column(DateTime)

    user_id = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"))

class NordPoolData(Base):
    id = Column(Integer, primary_key=True, index=True)
    last_update_time = Column(DateTime)
    min_price = Column(Float)
    max_price = Column(Float)
    avg_price = Column(Float)

class NordPoolPrices(Base):
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    price = Column(Float)