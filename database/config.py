import os
from dotenv import load_dotenv

from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class DatabaseSettings:
    PROJECT_NAME: str = "Victron-Energy Automation"
    PROJECT_VERSION: str = "1.0.0"

    DB_USER : str = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_SERVER : str = os.getenv("DB_SERVER")
    DB_PORT : str = os.getenv("DB_PORT") # default DB port is 5432
    DB_DB : str = os.getenv("DB_DB")
    #DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_DB}"

    TEST_DB_DB : str = os.getenv("TEST_DB_DB")
    TEST_DATABASE_URL : str = "sqlite:///test_db.db"
    #change db url to DB if we'd want to test with DB
    DATABASE_URL = TEST_DATABASE_URL
    #f"DBql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{TEST_DB_DB}"


settings = DatabaseSettings()