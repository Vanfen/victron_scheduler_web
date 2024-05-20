from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.models import Base
from victron.models import Base

from .config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()