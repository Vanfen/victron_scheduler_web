from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import base_class


Base = base_class.Base
class UserAuth(Base):
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    date_created = Column(DateTime(timezone=True))
    date_active = Column(DateTime(timezone=True))
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    session_token = Column(String, unique=True, nullable=True)
    refresh_token = Column(String, unique=True, nullable=True)

    reset_token = relationship("ResetToken", cascade="all, delete", backref="user_auth")
    victron_energy = relationship("VictronEnergy", cascade="all, delete", backref="user_auth")

class ResetToken(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"))
    expiry_time = Column(DateTime(timezone=True), default=datetime.utcnow)
    token = Column(String)
    used = Column(Boolean, default=False)